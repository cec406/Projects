#!/usr/bin/env python3
"""Check staged release artifacts and, optionally, a local HTTP endpoint."""

import argparse
from dataclasses import asdict, dataclass
import hashlib
import http.client
import json
from pathlib import Path
import platform
import re
from urllib.parse import urlsplit


ARCHES = {"amd64": "amd64", "x86_64": "amd64", "arm64": "arm64", "aarch64": "arm64"}
TIMEOUT = 3


@dataclass
class Check:
    name: str
    passed: bool
    detail: str


def load_manifest(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("release"), str) or not data["release"].strip():
        raise ValueError("manifest needs a non-empty release name")
    if data.get("architecture") not in ("amd64", "arm64"):
        raise ValueError("architecture must be amd64 or arm64")
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("manifest needs at least one artifact")
    seen = set()
    for entry in artifacts:
        if not isinstance(entry, dict):
            raise ValueError("each artifact must be an object")
        name, digest = entry.get("path"), entry.get("sha256")
        if not isinstance(name, str) or not name or Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("artifact paths must be relative and may not contain '..'")
        key = Path(name)
        if key in seen:
            raise ValueError(f"duplicate artifact path: {name}")
        seen.add(key)
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            raise ValueError(f"invalid SHA-256 for {name}")
    return data


def check_artifact(root, entry):
    name = entry["path"]
    try:
        path = (root / name).resolve()
        if not path.is_relative_to(root):
            return Check(name, False, "Path resolves outside staging directory. Replace the artifact with a staged file.")
        if not path.is_file():
            return Check(name, False, "Required file missing. Copy the approved artifact into staging.")
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        expected = entry["sha256"].lower()
        if actual != expected:
            return Check(name, False, f"SHA-256 mismatch. Restage from the approved release. Expected {expected}; got {actual}.")
        return Check(name, True, f"SHA-256 matches: {actual}.")
    except (OSError, RuntimeError, ValueError):
        return Check(name, False, "Could not read staged file. Check its path and permissions.")


def check_http(url):
    connection = None
    try:
        parsed = urlsplit(url)
        if (parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "::1"}
                or parsed.username is not None or parsed.password is not None or parsed.fragment):
            return Check("HTTP health", False, "Use an HTTP URL on 127.0.0.1 or [::1], with no credentials or fragment.")
        connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=TIMEOUT)
        target = parsed.path or "/"
        if parsed.query:
            target += "?" + parsed.query
        connection.request("GET", target)
        status = connection.getresponse().status
        if status != 200:
            return Check("HTTP health", False, f"HTTP {status}; expected 200. Check the rollout and port-forward.")
        return Check("HTTP health", True, "Local endpoint returned HTTP 200.")
    except (OSError, ValueError, http.client.HTTPException):
        return Check("HTTP health", False, "Could not reach the local endpoint. Check the rollout, URL, and port-forward.")
    finally:
        if connection is not None:
            connection.close()


def inspect(manifest, root, target_arch, health_url=None):
    expected = manifest["architecture"]
    target = ARCHES.get(target_arch.lower())
    checks = [Check("target architecture", target == expected,
                    f"Manifest: {expected}; target: {target or target_arch}."
                    + (" Select a release built for this target." if target != expected else ""))]
    checks.extend(check_artifact(root.resolve(), entry) for entry in manifest["artifacts"])
    staging_passed = all(check.passed for check in checks)
    if health_url is not None and staging_passed:
        checks.append(check_http(health_url))
    status = ("BLOCKED" if not all(check.passed for check in checks)
              else "HEALTH_CHECK_PASSED" if health_url is not None else "STAGING_PASSED")
    health = ("not requested" if health_url is None else "checked" if staging_passed
              else "skipped because staging failed")
    return {"release": manifest["release"], "status": status, "health": health,
            "checks": [asdict(check) for check in checks]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("staging", type=Path)
    parser.add_argument("--target-arch", default=platform.machine(), help="target architecture (defaults to this machine)")
    parser.add_argument("--health-url", help="optional post-deploy HTTP endpoint on literal loopback")
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        report = inspect(manifest, args.staging, args.target_arch, args.health_url)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(report, indent=2))
    return 1 if report["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
