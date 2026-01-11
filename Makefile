PROJECT_DIR:=autotriage

.PHONY: setup test lint web-build run demo docker-build docker-run
.PHONY: e2e perf verify

setup:
	$(MAKE) -C $(PROJECT_DIR) setup

test:
	$(MAKE) -C $(PROJECT_DIR) test

lint:
	$(MAKE) -C $(PROJECT_DIR) lint

web-build:
	$(MAKE) -C $(PROJECT_DIR) web-build

run:
	$(MAKE) -C $(PROJECT_DIR) run

demo:
	$(MAKE) -C $(PROJECT_DIR) demo

docker-build:
	$(MAKE) -C $(PROJECT_DIR) docker-build

docker-run:
	$(MAKE) -C $(PROJECT_DIR) docker-run

e2e:
	$(MAKE) -C $(PROJECT_DIR) e2e

perf:
	$(MAKE) -C $(PROJECT_DIR) perf

verify:
	$(MAKE) -C $(PROJECT_DIR) verify
