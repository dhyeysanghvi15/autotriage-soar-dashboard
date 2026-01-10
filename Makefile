PROJECT_DIR:=autotriage

.PHONY: setup test lint web-build run demo docker-build docker-run

setup:
\t$(MAKE) -C $(PROJECT_DIR) setup

test:
\t$(MAKE) -C $(PROJECT_DIR) test

lint:
\t$(MAKE) -C $(PROJECT_DIR) lint

web-build:
\t$(MAKE) -C $(PROJECT_DIR) web-build

run:
\t$(MAKE) -C $(PROJECT_DIR) run

demo:
\t$(MAKE) -C $(PROJECT_DIR) demo

docker-build:
\t$(MAKE) -C $(PROJECT_DIR) docker-build

docker-run:
\t$(MAKE) -C $(PROJECT_DIR) docker-run

