#!/usr/bin/env python3
"""Restore an approved fixture into a disposable loopback GrizzWorks server."""

import argparse
from decimal import Decimal
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
from urllib.error import URLError
from urllib.request import ProxyHandler, Request, build_opener
import uuid

from migrate import build_plan, summarize


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def verify(server):
    baseline = (FIXTURES / "baseline.json").read_bytes()
    source = (FIXTURES / "legacy-corrected.csv").read_bytes()
    report, result = build_plan(source, baseline)
    assert report["status"] == "READY_FOR_APPROVAL"
    replay, _ = build_plan(source, json.dumps(result).encode())
    assert replay["new"]["records"] == 0 and replay["already_present"] == report["accepted"]
    with tempfile.TemporaryDirectory(prefix="grizzworks-migration-") as directory:
        file = Path(directory) / "db.json"
        marker = f"Migration verification {uuid.uuid4()}"
        lab_baseline = json.loads(baseline)
        lab_baseline["settings"]["shopName"] = marker
        file.write_text(json.dumps(lab_baseline), encoding="utf-8")
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        origin = f"http://127.0.0.1:{port}"
        client = build_opener(ProxyHandler({}))

        def request(path, payload=None):
            data = None if payload is None else json.dumps(payload).encode()
            with client.open(Request(origin + path, data=data, headers={"Content-Type": "application/json"}), timeout=2) as response:
                return response.read()

        def start():
            return subprocess.Popen(["node", str(server)], cwd=server.parent,
                                    env={**os.environ, "HOST": "127.0.0.1", "PORT": str(port), "DATA_FILE": str(file)},
                                    stdout=subprocess.DEVNULL)

        def wait_for_own_instance(child):
            for _ in range(100):
                if child.poll() is not None:
                    raise RuntimeError(f"lab server exited with status {child.returncode}")
                try:
                    state = json.loads(request("/api/state"))
                except (OSError, URLError, ValueError):
                    time.sleep(0.05)
                    continue
                if state.get("settings", {}).get("shopName") != marker:
                    raise RuntimeError("loopback port does not belong to this lab; refusing to restore")
                return
            raise RuntimeError("lab server did not become ready")

        def stop(child):
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()

        child = start()
        try:
            wait_for_own_instance(child)
            before = json.loads(request("/api/export"))
            approved, candidate = build_plan(source, json.dumps(before).encode())
            assert approved["new"] == report["new"]
            assert json.loads(request("/api/import", candidate)) == {"ok": True}
            rows = json.loads(request("/api/workorders"))
            assert rows == candidate["workorders"], "restored rows did not match candidate"
            assert b"GrizzWorks" in request("/")
        finally:
            stop(child)

        child = start()
        try:
            wait_for_own_instance(child)
            rows_after_restart = json.loads(request("/api/workorders"))
            assert rows_after_restart == rows, "work orders did not persist across restart"
            example = json.loads(request("/api/workorders/wo-migration-l-101"))
        finally:
            stop(child)
    imported = [row for row in rows if row["id"] in set(report["planned_order_ids"])]
    assert summarize(imported) == report["new"]
    return {"scope": "Synthetic fixture in disposable GrizzWorks server; API verification, not customer data",
            "baseline_workorders": len(lab_baseline["workorders"]), "restored_workorders": len(rows),
            "imported": summarize(imported), "replay_new_workorders": replay["new"]["records"],
            "preserved_across_server_restart": True, "example_work_order": example}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("server", type=Path, help="path to applications/dashboard/server.js")
    args = parser.parse_args()
    print(json.dumps(verify(args.server.resolve(strict=True)), indent=2))
