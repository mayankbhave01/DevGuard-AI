# DevGuard AI — API Summary

Swagger UI is available locally at:

```text
http://localhost:8000/docs
```

Protected endpoints require:

```http
Authorization: Bearer <JWT>
```

## Authentication

- `POST /api/auth/register`
- `POST /api/auth/login`

## Scans

- `POST /api/scans` — submit and run a code review
- `GET /api/scans` — list scans owned by the current user
- `GET /api/scans/dashboard` — dashboard aggregates
- `GET /api/scans/{id}` — scan details and findings
- `DELETE /api/scans/{id}` — delete a scan

## Reporting

Per-scan exports support:

- PDF
- HTML
- Markdown
- JSON
- CSV
- TXT
- ZIP bundle containing all formats

The exact generated endpoint paths are documented interactively in Swagger and implemented in the scan/report API modules.

## System

- `GET /health`
- `GET /docs` — Swagger UI
