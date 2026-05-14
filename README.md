# VO2max / MPK Report

This repository combines:

1. Existing customer research/adaptation materials for VO2max reporting.
2. The current clean web MVP located in this workspace.

## Current Web MVP

The implemented MVP shows the path from diagnostic data to report:

- client creation and search;
- measurement history;
- legacy CSV import;
- manual data entry and editing;
- row sampling;
- threshold assignment;
- charts;
- training zones;
- report preview;
- HTML/PDF/DOCX-style report exports;
- local file-backed persistence for MVP.

## Run MVP

From this directory:

```powershell
cd backend
python run_8081.py
```

Open:

```text
http://127.0.0.1:8081
```

Port `8081` is used because `8080` may be occupied on some Windows machines.

## Checks

From `backend`:

```powershell
python -m unittest discover -s tests
```

Expected current result:

```text
28 tests OK
```

## Important Folders

```text
backend/     Current dependency-light MVP backend and tests
frontend/    Current web UI
samples/     Anonymized sample data
storage/     Local runtime storage placeholders
docs/        MVP phase notes and acceptance scenario
Research/    Customer deep research materials
```

## Customer Research Materials

The existing customer repository also contains:

- architecture notes;
- adaptation notes;
- research prompts and answers;
- earlier Django/reporting materials.

These materials are preserved in the merge for context and future development.

## Privacy Note

Do not commit raw diagnostic files, generated reports, personal data, or original legacy/C# source archives. Runtime storage folders are intentionally ignored except `.gitkeep` placeholders.

