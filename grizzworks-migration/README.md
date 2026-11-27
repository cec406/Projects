# GrizzWorks migration rehearsal

Move legacy work orders into a disposable GrizzWorks instance without guessing dates, dropping bad rows silently, or creating duplicates on replay. This Python CLI reviews a fictional shop’s CSV against an existing v2 backup and writes a **new candidate backup** only after approval. It never contacts a running server or edits the baseline.

**Review the evidence:** [Blocked preview](reports/blocked.json) · [Corrected preview](reports/approved-preview.json) · [Recorded Node/REST lab result](reports/lab-result.json) · [Portfolio case study](https://grizzlyse.com/portfolio/#migration)

## What happened in the rehearsal

1. The [messy export](fixtures/legacy-messy.csv) had five rows. The preview proposed one and rejected four: one ambiguous date, one unmapped customer, and both rows of a case-insensitive duplicate ID. Any rejection blocks the **entire** apply.
2. The [corrected export](fixtures/legacy-corrected.csv) resolved those issues. It mapped four work orders worth **7.50 estimated labor hours**, not billed hours or money. The original work order stayed in place.
3. The harness exported a disposable Node server’s backup, built the candidate, restored it through GrizzWorks’ actual API, and verified five work orders on the server, including four imported. It restarted the server and confirmed the same rows were still there. Planning the corrected CSV again against the migrated backup proposed **zero** new rows.

## Run it locally

Python 3.11+; no third-party dependencies. Run from this directory. The lab harness also needs Node.js 18+ and the sibling [`applications`](https://github.com/cec406/applications) checkout.

```sh
# Expected exit 1: rejected rows are printed, no output backup is written.
python3 -B migrate.py fixtures/legacy-messy.csv fixtures/baseline.json --preview

# Inspect the accepted count, hours, and proposed IDs before approving.
python3 -B migrate.py fixtures/legacy-corrected.csv fixtures/baseline.json --preview

# Replace APPROVAL_HASH with approval_sha256 from the corrected preview.
python3 -B migrate.py fixtures/legacy-corrected.csv fixtures/baseline.json \
  --apply /tmp/grizzworks-rehearsal.json --approve APPROVAL_HASH

# Expected: 0 new, 4 already present, 7.50 hours.
python3 -B migrate.py fixtures/legacy-corrected.csv /tmp/grizzworks-rehearsal.json --preview

python3 -B -m unittest -v
python3 -B verify_lab.py ../../applications/dashboard/server.js
```

`--apply` writes exclusively to a new path; it will fail if that path already exists. Exit `0` means preview/apply succeeded, `1` means row issues blocked apply, and `2` means an input, I/O, approval, or CLI error. The approval checksum ties the decision to exact CSV and backup bytes and the plan version. It is not an authentication or signing mechanism.

## Mapping and boundaries

- Exact CSV headers: `legacy_id,customer,job,title,status,priority,due,est_hours`. Matching ignores case and extra whitespace. A job must resolve uniquely within its customer; the tool does not create either record or guess.
- Explicit workflow status mappings: `open → Backlog`, `booked → Scheduled`, `active → In Progress`, `parts hold → Waiting Parts`, `closed → Done`. Dates must be `YYYY-MM-DD`; estimated hours must be nonnegative quarter-hour increments up to 10,000. Work order type is set to `Corrective` for this fixture workflow.
- Stable IDs use `wo-migration-<lowercase legacy_id>`. An exact existing match is skipped; an existing ID with different mapped values is rejected rather than overwritten. The rehearsal assumes a single source system; multiple sources would need distinct ID namespaces. Source timestamps, attachments, invoices, and payments aren’t migrated.
- The [lab harness](verify_lab.py) starts its own Node child process, binds to loopback, uses a temporary data file, verifies instance identity before restore, and cleans up afterward. The report verifies app data through the REST API, not a production rollout.

## Cutover and fallback

For a rehearsal, retain the unchanged baseline, correct rejected rows with the data owner, and compare counts, accepted hours, and a sampled work order on the **Work Orders** board (`/#/workorders`) before signing off. To view the generated backup, use **Settings → Data & Backups → Restore backup** on a disposable GrizzWorks instance or a clean, disposable browser profile with fictional data only. Restore replaces the **entire** database. Never point the lab workflow at a live shop or restore over records you need.

A real cutover would require a tested baseline restore, an authorized maintenance window, a write freeze and fresh export, review of access and data handling, an owner for any rejections, and a rollback decision before users begin entering new records. Once new writes start, restoring an old backup can discard them; plan how those writes would be reconciled before rollback. None of those production steps are claimed as exercised here.
