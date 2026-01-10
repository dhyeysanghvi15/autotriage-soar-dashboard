PY:=python3
VENV?=.venv
PIP:=$(VENV)/bin/pip
PYTHON:=$(VENV)/bin/python

.PHONY: setup test lint web-build run demo docker-build docker-run

setup:
	$(PY) -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -e ".[dev]"
	cd web && npm ci

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .
	$(PYTHON) -m mypy autotriage

web-build:
	cd web && npm run build
	rm -rf autotriage/autotriage/app/static
	mkdir -p autotriage/autotriage/app/static
	cp -R web/dist/* autotriage/autotriage/app/static/

run:
	$(PYTHON) -m autotriage.cli.main run --mode all

demo:
	$(PYTHON) -m autotriage.cli.main demo

docker-build:
	docker build -t autotriage:latest -f docker/Dockerfile .

docker-run:
	docker run --rm -p 8080:8080 autotriage:latest
