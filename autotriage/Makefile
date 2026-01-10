PY:=python3
VENV?=.venv
PIP:=$(VENV)/bin/pip
PYTHON:=$(VENV)/bin/python

.PHONY: setup test lint web-build run demo docker-build docker-run

setup:
\t$(PY) -m venv $(VENV)
\t$(PIP) install -U pip
\t$(PIP) install -e ".[dev]"
\tcd web && npm install

test:
\t$(PYTHON) -m pytest -q

lint:
\t$(PYTHON) -m ruff check .
\t$(PYTHON) -m ruff format --check .
\t$(PYTHON) -m mypy autotriage

web-build:
\tcd web && npm run build
\trm -rf autotriage/app/static
\tmkdir -p autotriage/app/static
\tcp -R web/dist/* autotriage/app/static/

run:
\t$(PYTHON) -m autotriage.cli.main run --mode all

demo:
\t$(PYTHON) -m autotriage.cli.main demo

docker-build:
\tdocker build -t autotriage:latest -f docker/Dockerfile .

docker-run:
\tdocker run --rm -p 8080:8080 autotriage:latest

