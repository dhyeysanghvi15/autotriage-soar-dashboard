# Threat Model (Demo)

This demo prioritizes determinism and auditability over hardening:

- SQLite is file-based; treat the DB file as sensitive.
- Webhook ingestion is unauthenticated by default; enable auth in front of the container for real use.
- Enrichers use offline datasets; no external network calls are required.

