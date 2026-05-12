# Backend

Backend core for VO2max / MPK Report.

The current implementation intentionally uses only Python standard library modules. This keeps the parser, domain layer, API facade and local HTTP server easy to test before choosing the final production framework.

Possible production stack:

- Python backend API;
- PostgreSQL;
- parser layer;
- report layer;
- file storage for raw uploads and generated reports.

## Implemented

- domain entities for clients, measurements, measurement items, thresholds, raw files, audit events;
- legacy CSV parser based on the original C# `MeasurementItemMap`;
- import service with preview diagnostics and raw file copy support;
- client service, measurement service and workspace presenter;
- application API facade;
- local HTTP server;
- minimal frontend screen for client creation, CSV import and table editing;
- browser CSV upload endpoint;
- chart service for HR, ventilation, VO2 and lactate;
- comparison data for several measurements;
- threshold service for manual MAM/AEP/ANP/DO2/VO2max points;
- basic training zones;
- report service with HTML/PDF/DOCX export;
- comparison blocks in reports;
- file-backed repository for local persistence;
- unit tests for parser, import, workflow, API, HTTP smoke and persistence.
