# VO2max / MPK Report App

This directory is the clean product workspace for the web version.

## Current Phase

Implemented baseline for phases 0-2:

- project structure;
- backend domain models;
- legacy CSV parser;
- import preview service;
- anonymized sample CSV;
- unit tests.

Detailed completion note: `docs/PHASE_0_2_SUMMARY.md`.

Implemented baseline for phases 3-4:

- client service;
- client search and profile;
- measurement history;
- import into a specific client profile;
- dependency-free application API;
- minimal HTTP server;
- minimal browser UI for the main measurement workspace;
- file-backed repository for local persistence;
- workspace service for the main measurement screen;
- editable measurement items;
- row sampling;
- rated power recalculation;
- audit events for imports and manual edits;
- frontend-ready workspace view model.

Detailed completion note: `docs/PHASE_3_4_SUMMARY.md`.

Implemented baseline for phases 5-6:

- chart service;
- HR, ventilation, VO2 and lactate chart data;
- comparison of several measurements for one client;
- manual threshold assignment;
- lactate editing through the measurement table;
- basic training zones;
- frontend SVG charts;
- threshold markers on charts.

Detailed completion note: `docs/PHASE_5_6_SUMMARY.md`.

Implemented baseline for phases 7-9:

- report snapshot;
- browser CSV upload;
- HTML preview;
- HTML, PDF and DOCX export;
- comparison block in reports;
- simple DOCX template layer;
- report download endpoints;
- report actions in the browser UI;
- acceptance demo scenario;
- full MVP test coverage.

Detailed completion note: `docs/PHASE_7_9_SUMMARY.md`.
Acceptance path: `docs/ACCEPTANCE_DEMO_SCENARIO.md`.

## Structure

```text
app/
  backend/
    vo2max/
      domain/
      parsers/
      services/
    tests/
  frontend/
  docs/
  samples/
  storage/
    raw_files/
    reports/
```

## Run Backend Tests

From `app/backend`:

```powershell
python -m unittest discover -s tests
```

## Run Local App

From `app/backend`:

```powershell
python -m vo2max.api.server
```

Then open:

```text
http://127.0.0.1:8080
```

The local app stores raw files and its local state under `app/storage`.

## Data Safety

Do not commit real patient/athlete files, raw diagnostic files, generated reports, or exports with personal data.
