# AutoTriage — Cybersecurity Automation + SOAR Demo

> **10-second pitch:** AutoTriage runs a deterministic SOAR pipeline (ingest, normalize, fingerprint, dedup, correlate, enrich, score, decide, route, ticket) with append-only event sourcing, Prometheus metrics, replay experiments, and a React dashboard all under one FastAPI URL.

**One URL demo:**

- Dashboard: `/` (static React app served by FastAPI)
- API: `/api/*`
- Webhook ingest: `/webhook/alerts`
- Prometheus: `/metrics`

## Quickstart

### Docker

```bash
make docker-build
make docker-run
```

Open `http://localhost:8080` to see the dashboard served from the same FastAPI process.

### Local development

```bash
make setup
make web-build
make run
```

In a separate terminal:

```bash
python -m autotriage.cli.main ingest-file data/sample_alerts/vendor_a.jsonl
```

## Demo recipe (deterministic)

- `make demo` seeds the DB, generates 200 alerts (`demo_seed=1337`), ingests them, and prints the dashboard URL.
- The demo keeps the API + worker running so you can explore; stop with `Ctrl+C`.
- Reproduce exactly with `python -m autotriage.cli.main tools alert-generator --seed 1337 --n 200 --out data/sample_alerts/generated.jsonl`.
- The alert generator is deterministic (seed + vendor shapes) so you can replay demos or experiments reliably.

## Testing & performance

- Requirements: Python 3.11+ and Node 20+ (CI uses Node 20).
- `make lint` (ruff + mypy) and `make test` (pytest).
- `make web-build` verifies the Vite build and copies `web/dist` into `autotriage/app/static`.
- `make e2e` runs Playwright UI tests against the seeded backend.
- `make perf` uses `autotriage.tools.perf_run` to ingest 1,000 alerts, waits for the worker, and measures ingest RPS, exhaustion of dedup/correlation, case/ticket totals, and deadletters. Failures occur when processing is too slow or deadletters accumulate.
- `make verify` chains lint → test → web-build → e2e.
- For full coverage mapping, see `TEST_PLAN.md` (scope + matrix) and `TEST_REPORT.md` (commands + results).

## Dashboard tour

1. **Overview**: key cards (ingested, deduped, correlated, auto-closed, tickets, errors) feed off `/api/overview`.
2. **Cases**: interactive filters (search, severity, decision, queue, time window) drive `/api/cases`.
3. **Detail**: timeline, entity graph, enrichments, scoring explainability, routing rationale, and actionable playbooks (served from `/playbooks/` guarded to Markdown files only).
4. **Experiments**: replay results stored via `/api/replay` compare dedup reduction, ticket reduction, and decision distribution before/after.

## Architecture

```mermaid
flowchart LR
  subgraph Ingestion
    A[Webhook /webhook/alerts] --> B[(SQLite alerts queue)]
  end
  B --> C[Worker: pipeline orchestrator]
  C --> D[(SQLite event store)]
  C --> E[(SQLite cases + entities + edges)]
  C --> F[(SQLite tickets)]
  subgraph APIs
    G[FastAPI /api/*, /metrics, /healthz]
    H[Static dashboard (Vite/React)]
  end
  G --> E
  G --> D
  H -->|same-origin| G
  G --> I[/metrics Prometheus/]
  C --> G
  G --> J[/playbooks/*.md (limited)]
```

## What this demonstrates

- SOAR-like pipeline with stage-level audit trail (SQLite events) and replay experiments.
- Idempotent webhook ingestion (header key or stable computed key).
- Deduplication windows + correlation by entity overlap (user/host/ip/domain/rule/technique).
- Offline, deterministic enrichment (WHOIS, Geo/ASN, IP reputation, allowlist, asset inventory) with cache TTL, rate limiting, and circuit breaker.
- Explainable scoring + decisioning + routing (contributions and rationale exposed in the UI).
- Production discipline: tests (unit/integration/e2e), perf sanity harness, CI, Docker, Prometheus metrics.

## API contract summary

- `GET /healthz` → `{status, version}`.
- `GET /readyz` → `{status, db}`.
- `GET /metrics` → Prometheus counters/histograms (`autotriage_ingest_total`, `autotriage_pipeline_stage_total`, etc.).
- `POST /webhook/alerts` → normalized vendor payloads (A/B/C). Idempotent via `Idempotency-Key` header or computed hash; responds `{ingest_id, status}`.
- `GET /api/overview` → dashboard stats (ingested/deduped/cases/auto_closed/tickets/errors).
- `GET /api/cases` → `time_range`, `severity_min`, `decision`, `queue`, `q` (search) filters.
- `GET /api/cases/{case_id}` → case metadata, timeline, entity graph, enrichments, scoring/routing explainability, ticket + playbook actions.
- `POST /api/replay` → run a replay experiment, returns `experiment_id`.
- `GET /api/experiments` & `/api/experiments/{id}` → stored before/after metrics, timeseries, distributions.
- `GET /api/config` → effective config (version, rules_dir, data_dir, windows, enabled enrichers).

## Deterministic data sources

- `data/sample_alerts/` contains vendor-specific JSONL slices for demos.
- `data/mock_*.csv` / YAML (allowlists, asset inventory, reputation, WHOIS, geo/ASN) back the enrichment cache.
- Enrichers use SQLite cache + TTL + rate limit + circuit breaker, so repeated runs behave consistently.
- Replay experiments ingest stored events with new config overrides to compare outcomes.

## Repo map

- `autotriage/autotriage/app`: FastAPI app, routes, static hosting, playbook serving
- `autotriage/autotriage/core`: normalize/fingerprint/dedup/correlate/enrich/score/route pipeline
- `autotriage/autotriage/enrichers`: offline enrichers + cache + rate limit + breaker
- `autotriage/autotriage/storage`: SQLite migrations + repositories + aggregates
- `autotriage/web`: React dashboard (Vite)
- `autotriage/.github/workflows/ci.yml`: CI (lint, tests, web build, Playwright e2e, Docker build)

## Known issues

- `web/` dev dependencies surface 2 moderate `npm audit` advisories (transitive). They appear during builds (`npm run build`) but fixing them requires a major Vite upgrade; documented in `autotriage/docs/runbook.md`.
- `make perf` assumes the worker can empty 1,000 alerts in ~120s; slower machines may need higher `completion_timeout_s`.

## Roadmap

- [x] Single-container FastAPI + Vite with same-origin dashboard.
- [x] Event-sourced SOAR pipeline w/ dedup/correlation.
- [x] Replays + experiments + metrics.
- [x] Playwright-driven UI verification + screenshot automation.
- [ ] Expand experiments dashboard with scenario comparisons.
- [ ] Add SOC-ready alerts connector stubs (Splunk/QRadar).
- [ ] Succinct video capture instructions (future screencast).

## Skills demonstrated

- Python 3.11+ FastAPI microservice with Typer CLI, SQLite persistence, and structured logging.
- Deterministic aggregator pipeline (normalization, fingerprinting, dedup windows, entity correlation).
- Offline enrichers with cache/rate-limit/circuit-breaker guardrails.
- Explaining decisions (score contributions, routing rationale) and storing events for replay.
- Vite+React dashboard with Playwright e2e and same-origin SPA hosting.
- Ops maturity: linting, type checking, tests (unit/integration/e2e), perf harness, Docker + CI.
