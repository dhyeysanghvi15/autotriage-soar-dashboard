# Changelog

## v1.0.0

- Single-container demo: FastAPI serves `/api/*`, `/metrics`, and the built dashboard at `/` (same-origin, no CORS).
- SOAR pipeline: ingest → normalize → fingerprint → dedup → correlate → enrich → score → decide → route → ticket/close with append-only SQLite events.
- Deterministic offline enrichments (WHOIS/IP reputation/GeoASN/allowlist/asset context) with cache, rate limiting, and circuit breaker.
- Replay experiments API with stored before/after summaries.
- Testing phase complete: unit/integration/API contract tests, Playwright E2E, and `make perf` sanity harness with `TEST_PLAN.md` + `TEST_REPORT.md`.
- CI (ruff + mypy + pytest + web build + docker build), Make targets, and Docker multi-stage build.
