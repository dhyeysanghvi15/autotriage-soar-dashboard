# TEST REPORT — AutoTriage (Full Testing Phase)

## Environment

- OS: macOS (Darwin 25.1.0, arm64)
- Python: 3.14.0 (`autotriage/.venv`)
- Node: v25.2.1
- npm: 11.6.2
- Docker: 29.1.3

## Commands run

- `make lint`: pass
- `make test`: pass (26 tests)
- `make web-build`: pass
- `make e2e`: pass (3 tests)
- `make perf`: pass (1000 alerts)
- `make verify`: pass
- `make docker-build`: pass
- Docker smoke:
  - `GET /healthz`: 200
  - `GET /api/overview`: 200
  - `POST /webhook/alerts`: 202

## Results summary

- Unit tests: pass (fingerprint/dedup/routing/scoring/static safety/cache TTL/circuit breaker/correlation)
- Integration tests: pass (webhook idempotency, dedup+correlation, API contract, replay experiment, deadletter on enricher failure)
- E2E tests: pass (overview renders, cases+detail flow, playbook markdown 200)
- Performance sanity: pass
  - Example output: `{"n":1000,"ingest_seconds":3.195,"ingest_rps":312.9,"processing_seconds":0.206,"cases":3,"tickets":3,"deduped":991,"failed_events":0,"deadletters":0}`
- Docker smoke: pass

## Issues found + fixes applied

- `make perf` timed out initially due to worker throttling (`worker_loop` slept every iteration). Fixed `autotriage/autotriage/worker.py` to sleep only when idle; perf harness now completes under defaults.
- Some aborted Playwright runs can leave the local test server listening on port `18080`, which makes subsequent E2E appear to “hang”. The E2E harness now removes stale state and fails fast if the port is already in use.
- Docker build logs show `npm audit` moderate vulnerabilities in transitive web dev dependencies (already documented in `autotriage/README.md` and `autotriage/docs/runbook.md`).
- `make demo` error handling was tightened to avoid stray background tasks and to fail clearly if the local API never becomes ready.

## Sign-off checklist

- [x] Repo green (`make verify`)
- [x] E2E passes deterministically
- [x] Perf harness passes with defaults
- [x] Docker smoke validated
- [x] Docs updated for test running
