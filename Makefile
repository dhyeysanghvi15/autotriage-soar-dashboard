PROJECT_DIR:=autotriage

.PHONY: setup test lint web-build run demo docker-build docker-run

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
