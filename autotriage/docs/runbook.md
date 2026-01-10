# Runbook

## Start

- Local: `make setup && make web-build && make run`
- Docker: `make docker-build && make docker-run`

## Health

- `GET /healthz`, `GET /readyz`
- Prometheus metrics: `GET /metrics`

## Common issues

- If the dashboard shows no data, run `make demo` to seed and ingest synthetic alerts.

