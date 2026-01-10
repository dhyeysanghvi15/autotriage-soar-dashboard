# Runbook

## Start

- Local: `make setup && make web-build && make run`
- Docker: `make docker-build && make docker-run`

## Health

- `GET /healthz`, `GET /readyz`
- Prometheus metrics: `GET /metrics`

## Common issues

- If the dashboard shows no data, run `make demo` to seed and ingest synthetic alerts.

## Known issues

- `npm audit` (dev deps): `cd web && npm audit` reports an `esbuild` advisory; the non-breaking fix is not available (would require a Vite major upgrade via `npm audit fix --force`). Re-check later by upgrading Vite and verifying `npm run build`.
