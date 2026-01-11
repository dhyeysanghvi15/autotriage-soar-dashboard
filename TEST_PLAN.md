# TEST PLAN — AutoTriage (Full Testing Phase)

## Scope

- Backend correctness: ingestion, idempotency, normalization, fingerprinting, deduplication, correlation, enrichment, scoring/decisioning, routing, ticketing, replay experiments, metrics.
- Dashboard correctness: same-origin SPA loads, pages render, API integration works, playbook markdown served.
- Reliability: worker processing behavior, deadletter behavior, enricher cache/TTL, rate limit + circuit breaker behavior.
- Performance sanity: ingest/processing throughput baseline (non-flaky, wide thresholds).
- Release readiness: docs, reproducible demo, smoke scripts, CI signals.

## Test matrix

| Area | Suite | Location | Runner |
|---|---|---|---|
| Backend logic | unit | `autotriage/autotriage/tests/unit` | `pytest` |
| Backend workflows | integration | `autotriage/autotriage/tests/integration` | `pytest` |
| API contract | integration | `autotriage/autotriage/tests/integration` | `pytest` |
| Dashboard | e2e | `autotriage/web/e2e` | `playwright` |
| Smoke | scripts | `autotriage/autotriage/tools` | `python -m ...` |
| Performance sanity | harness | `autotriage/autotriage/tools/perf_run.py` | `python -m ...` |
| Security basics | unit | traversal tests | `pytest` |

## How to run

- Backend:
  - Lint/typecheck: `make lint`
  - Unit+integration: `make test`
- Web build: `make web-build`
- E2E: `make e2e`
- Performance: `make perf`
- Full verification: `make verify`

## Pass/fail criteria

- `make lint` passes (ruff + mypy).
- `make test` passes and is deterministic.
- `make web-build` passes.
- `make e2e` passes (Playwright suite: 2–5 tests, deterministic DB seed).
- `make perf` passes default thresholds on a typical laptop.
- Docker smoke: container boots; `/healthz`, `/api/overview`, `/webhook/alerts` succeed.

## Known limitations

- Performance harness is a sanity check with wide thresholds (not a benchmark).
- Replay experiments validate stored summaries/diffs (not full “ground truth” labeling).
- Web `npm audit` may report dev-dependency advisories; production image does not ship Node tooling.

