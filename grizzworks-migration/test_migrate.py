import json
from pathlib import Path
import tempfile
from unittest import TestCase, mock

from migrate import build_plan, main


FIXTURES = Path(__file__).resolve().parent / "fixtures"
BASELINE = FIXTURES / "baseline.json"
MESSY = FIXTURES / "legacy-messy.csv"
CORRECTED = FIXTURES / "legacy-corrected.csv"


class MigrationTests(TestCase):
    def test_messy_export_fails_with_reviewable_reasons(self):
        report, _ = build_plan(MESSY.read_bytes(), BASELINE.read_bytes())
        self.assertEqual(report["source_rows"], 5)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual([row["line"] for row in report["rejected"]], [3, 4, 5, 6])
        self.assertIn("ambiguous dates", report["rejected"][0]["reason"])
        self.assertIn("customer", report["rejected"][1]["reason"])
        self.assertTrue(all("duplicate" in row["reason"] for row in report["rejected"][2:]))

    def test_corrected_export_preserves_baseline_and_reconciles(self):
        report, output = build_plan(CORRECTED.read_bytes(), BASELINE.read_bytes())
        self.assertEqual(report["accepted"], {"records": 4, "estimated_hours": "7.50"})
        original = json.loads(BASELINE.read_bytes())
        self.assertEqual(output["workorders"][0], original["workorders"][0])
        self.assertEqual(output["customers"], original["customers"])
        self.assertEqual(output["workorders"][1]["title"], "Inspect hoses, clamps, and fittings")
        self.assertEqual(output["workorders"][2]["jobId"], "job-lab-river")
        self.assertEqual(output["workorders"][2]["status"], "Waiting Parts")

    def test_exact_replay_does_not_duplicate(self):
        _, output = build_plan(CORRECTED.read_bytes(), BASELINE.read_bytes())
        report, replayed = build_plan(CORRECTED.read_bytes(), json.dumps(output).encode())
        self.assertEqual(report["new"]["records"], 0)
        self.assertEqual(report["already_present"], {"records": 4, "estimated_hours": "7.50"})
        self.assertEqual(replayed, output)

    def test_existing_changed_order_is_not_overwritten(self):
        _, output = build_plan(CORRECTED.read_bytes(), BASELINE.read_bytes())
        output["workorders"][1]["status"] = "Done"
        report, replayed = build_plan(CORRECTED.read_bytes(), json.dumps(output).encode())
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("no overwrite", report["rejected"][0]["reason"])
        self.assertEqual(replayed, output)

    def test_ambiguous_job_never_guesses(self):
        backup = json.loads(BASELINE.read_bytes())
        backup["jobs"].append({**backup["jobs"][0], "id": "job-lab-other"})
        report, _ = build_plan(CORRECTED.read_bytes(), json.dumps(backup).encode())
        self.assertEqual(len(report["rejected"]), 3)
        self.assertTrue(all("linked to that customer" in row["reason"] for row in report["rejected"]))

    def test_cli_requires_current_approval_and_never_overwrites_or_applies_rejects(self):
        report, _ = build_plan(CORRECTED.read_bytes(), BASELINE.read_bytes())
        with tempfile.TemporaryDirectory() as directory, mock.patch("sys.stdout"), mock.patch("sys.stderr"):
            out = Path(directory) / "output.json"
            options = [str(BASELINE), "--apply", str(out), "--approve", report["approval_sha256"]]
            self.assertEqual(main([str(MESSY), *options]), 1)
            self.assertFalse(out.exists())
            with self.assertRaises(SystemExit):
                main([str(CORRECTED), *options[:-1], "stale"])
            self.assertFalse(out.exists())
            self.assertEqual(main([str(CORRECTED), *options]), 0)
            expected = out.read_bytes()
            with self.assertRaises(SystemExit):
                main([str(CORRECTED), *options])
            self.assertEqual(out.read_bytes(), expected)
