import json
from pathlib import Path
import subprocess
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from unittest import TestCase, mock

from readiness import inspect, load_manifest, main


ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"


class Probe(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200 if self.path == "/ready" else 503)
        self.end_headers()

    def log_message(self, *args):
        pass


class ReadinessTests(TestCase):
    def setUp(self):
        self.manifest = load_manifest(FIXTURES / "release.json")

    def test_staging_pass_does_not_claim_a_health_check(self):
        report = inspect(self.manifest, FIXTURES / "staged", "x86_64")
        self.assertEqual(report["status"], "STAGING_PASSED")
        self.assertEqual(report["health"], "not requested")
        self.assertTrue(all(check["passed"] for check in report["checks"]))

    def test_bad_hash_stops_before_health_check(self):
        with mock.patch("readiness.check_http") as probe:
            report = inspect(self.manifest, FIXTURES / "broken", "amd64", "http://127.0.0.1:8080/")
        probe.assert_not_called()
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("SHA-256 mismatch", report["checks"][1]["detail"])
        self.assertTrue(report["checks"][2]["passed"])

    def test_missing_file_and_incompatible_architecture(self):
        with tempfile.TemporaryDirectory() as directory:
            report = inspect(self.manifest, Path(directory), "aarch64")
        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["checks"][0]["passed"])
        self.assertIn("Required file missing", report["checks"][1]["detail"])

    def test_manifest_rejects_unsafe_path(self):
        self.manifest["artifacts"][0]["path"] = "../other-file"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "release.json"
            path.write_text(json.dumps(self.manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "artifact paths"):
                load_manifest(path)

    def test_symlink_outside_staging_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "airgap-web.fixture").symlink_to(FIXTURES / "staged" / "airgap-web.fixture")
            report = inspect(self.manifest, root, "amd64")
        self.assertIn("outside staging directory", report["checks"][1]["detail"])

    def test_local_http_success_and_unhealthy_response(self):
        with HTTPServer(("127.0.0.1", 0), Probe) as server:
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                url = f"http://127.0.0.1:{server.server_port}"
                passed = inspect(self.manifest, FIXTURES / "staged", "amd64", url + "/ready")
                failed = inspect(self.manifest, FIXTURES / "staged", "amd64", url + "/not-ready")
            finally:
                server.shutdown()
                thread.join()
        self.assertEqual(passed["status"], "HEALTH_CHECK_PASSED")
        self.assertEqual(failed["status"], "BLOCKED")
        self.assertIn("HTTP 503", failed["checks"][-1]["detail"])

    def test_non_loopback_probe_is_rejected(self):
        with mock.patch("readiness.http.client.HTTPConnection") as connect:
            report = inspect(self.manifest, FIXTURES / "staged", "amd64", "http://example.com/")
        connect.assert_not_called()
        self.assertEqual(report["status"], "BLOCKED")

    def test_cli_exit_codes_and_json(self):
        for folder, code, snapshot in [("staged", 0, "staged.json"), ("broken", 1, "blocked.json")]:
            with self.subTest(folder=folder):
                run = subprocess.run([sys.executable, str(ROOT / "readiness.py"), str(FIXTURES / "release.json"),
                                      str(FIXTURES / folder), "--target-arch", "amd64"],
                                     capture_output=True, text=True, check=False)
                self.assertEqual(run.returncode, code, run.stderr)
                self.assertEqual(json.loads(run.stdout)["status"], "BLOCKED" if code else "STAGING_PASSED")
                self.assertEqual(json.loads(run.stdout), json.loads((ROOT / "reports" / snapshot).read_text(encoding="utf-8")))

    def test_invalid_manifest_exits_two(self):
        with mock.patch("sys.stderr"):
            with self.assertRaises(SystemExit) as error:
                main([str(FIXTURES / "no-such-manifest.json"), str(FIXTURES / "staged")])
        self.assertEqual(error.exception.code, 2)
