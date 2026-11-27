#!/usr/bin/env python3
"""Preview and reconcile a legacy work-order CSV into a new GrizzWorks backup."""

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import re


COLUMNS = ("legacy_id", "customer", "job", "title", "status", "priority", "due", "est_hours")
STATUSES = {"open": "Backlog", "booked": "Scheduled", "active": "In Progress",
            "parts hold": "Waiting Parts", "closed": "Done"}
PRIORITIES = {p.casefold(): p for p in ("Low", "Normal", "High", "Urgent")}


def key(value):
    return " ".join(value.split()).casefold()


def summarize(orders):
    return {"records": len(orders), "estimated_hours": str(sum(
        (Decimal(str(order["estHours"])) for order in orders), Decimal("0.00")).quantize(Decimal("0.00")))}


def build_plan(csv_bytes, backup_bytes):
    backup = json.loads(backup_bytes)
    if (not isinstance(backup, dict) or not isinstance(backup.get("meta"), dict)
            or backup["meta"].get("version") != 2 or not isinstance(backup.get("settings"), dict)):
        raise ValueError("expected a GrizzWorks v2 backup (not the /api/state snapshot)")
    for name in ("customers", "jobs", "workorders"):
        records = backup.get(name)
        if (not isinstance(records, list) or any(not isinstance(r, dict) or not isinstance(r.get("id"), str)
                                                 or not r["id"] for r in records)):
            raise ValueError(f"backup needs a {name} list with record IDs")
        if len({r["id"] for r in records}) != len(records):
            raise ValueError(f"duplicate record ID in backup collection: {name}")

    reader = csv.reader(io.StringIO(csv_bytes.decode("utf-8-sig"), newline=""), strict=True)
    if tuple(next(reader, [])) != COLUMNS:
        raise ValueError("expected CSV columns: " + ", ".join(COLUMNS))
    rows = [(reader.line_num, raw) for raw in reader if any(raw)]
    ids = Counter(key(raw[0]) for _, raw in rows if len(raw) == len(COLUMNS) and raw[0].strip())
    customers = defaultdict(list)
    jobs = defaultdict(list)
    for record in backup["customers"]:
        customers[key(str(record.get("name", "")))].append(record["id"])
    for record in backup["jobs"]:
        jobs[(record.get("customerId"), key(str(record.get("title", ""))))].append(record["id"])
    existing = {order["id"]: order for order in backup["workorders"]}
    added, matched, rejected = [], [], []
    for line, raw in rows:
        legacy = raw[0].strip() if raw else ""
        try:
            if len(raw) != len(COLUMNS):
                raise ValueError("wrong column count")
            row = dict(zip(COLUMNS, (part.strip() for part in raw)))
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", legacy):
                raise ValueError("legacy_id must be 1–64 letters, digits, underscores, or hyphens")
            if ids[key(legacy)] > 1:
                raise ValueError("duplicate legacy ID; resolve all duplicates in the source")
            if not row["title"]:
                raise ValueError("missing work-order title")
            customer_ids = customers[key(row["customer"])] if row["customer"] else []
            if len(customer_ids) != 1:
                raise ValueError("customer must match exactly one backup record")
            job_ids = jobs[(customer_ids[0], key(row["job"]))] if row["job"] else []
            if len(job_ids) != 1:
                raise ValueError("job must match exactly one job linked to that customer")
            if key(row["status"]) not in STATUSES or key(row["priority"]) not in PRIORITIES:
                raise ValueError("status or priority is not mapped")
            if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", row["due"]):
                raise ValueError("due date must be YYYY-MM-DD; ambiguous dates are not inferred")
            if not re.fullmatch(r"[0-9]{1,5}(\.[0-9]{1,2})?", row["est_hours"]):
                raise ValueError("estimated hours must be a plain decimal number")
            hours = Decimal(row["est_hours"])
            if not 0 <= hours <= 10000 or hours % Decimal("0.25"):
                raise ValueError("estimated hours must be 0–10000 in quarter-hour increments")
            order = {"id": f"wo-migration-{legacy.lower()}", "title": row["title"],
                     "status": STATUSES[key(row["status"])], "priority": PRIORITIES[key(row["priority"])],
                     "jobId": job_ids[0], "type": "Corrective", "due": date.fromisoformat(row["due"]).isoformat(),
                     "estHours": float(hours), "description": f"Imported legacy work order {legacy}."}
            old = existing.get(order["id"])
            if old is None:
                added.append(order)
            elif all(old.get(field) == value for field, value in order.items()):
                matched.append(order)
            else:
                raise ValueError("target ID already exists with different values; no overwrite")
        except (ValueError, InvalidOperation) as error:
            rejected.append({"line": line, "legacy_id": legacy, "reason": str(error)})

    digest = hashlib.sha256(b"grizzworks-migration-v1\0" + hashlib.sha256(csv_bytes).digest()
                            + hashlib.sha256(backup_bytes).digest()).hexdigest()
    report = {"status": "BLOCKED" if rejected else "READY_FOR_APPROVAL", "approval_sha256": digest,
              "source_rows": len(rows), "baseline_workorders": len(existing), "new": summarize(added),
              "already_present": summarize(matched), "accepted": summarize(added + matched),
              "rejected": rejected,
              "planned_order_ids": [order["id"] for order in added],
              "matched_order_ids": [order["id"] for order in matched]}
    backup["workorders"].extend(added)
    return report, backup


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("baseline", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preview", action="store_true")
    mode.add_argument("--apply", type=Path, metavar="NEW_BACKUP")
    parser.add_argument("--approve", help="approval_sha256 copied from the reviewed preview")
    args = parser.parse_args(argv)
    try:
        report, result = build_plan(args.csv_file.read_bytes(), args.baseline.read_bytes())
        if args.apply and report["rejected"]:
            print(json.dumps(report, indent=2))
            return 1
        if args.apply:
            if args.approve != report["approval_sha256"]:
                parser.error("run preview and approve its current approval_sha256")
            rendered = json.dumps(result, indent=2, allow_nan=False) + "\n"
            with args.apply.open("x", encoding="utf-8") as file:
                file.write(rendered)
            report["status"] = "BACKUP_WRITTEN"
            report["output_workorders"] = len(result["workorders"])
    except (OSError, ValueError, csv.Error) as error:
        parser.error(str(error))
    print(json.dumps(report, indent=2))
    return 1 if report["rejected"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
