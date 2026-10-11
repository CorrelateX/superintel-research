SHELL := /bin/bash
PYTHON := .venv/bin/python
PIP := .venv/bin/pip
COMPOSE := docker compose -f docker-compose.research.yml
DB_USER ?= superintel_research
DB_PASSWORD ?= superintel_research
DB_NAME ?= superintel_research
DB_PORT ?= 5433
DB_URL ?= postgresql://$(DB_USER):$(DB_PASSWORD)@127.0.0.1:$(DB_PORT)/$(DB_NAME)

# =============================================================================
# SuperIntel Research — Public Control Panel
# =============================================================================
# Research and paper-simulation subset of the larger private project's workflow.
# Live brokers, private alpha, production deployment, and orchestration are absent.
# =============================================================================

.DEFAULT_GOAL := help

.PHONY: help setup bootstrap demo demo-db demo-synthetic demo-paper backend
.PHONY: db-up db-down db-reset db-migrate db-seed db-shell db-status
.PHONY: test coverage lint audit ci clean

help:
	@echo ""
	@echo "╔══════════════════════════════════════════════════════╗"
	@echo "║       SUPERINTEL RESEARCH — PUBLIC CONTROL PANEL    ║"
	@echo "╠══════════════════════════════════════════════════════╣"
	@echo "║  SETUP                                               ║"
	@echo "║    make setup          Python environment + deps     ║"
	@echo "║    make bootstrap      setup + Timescale + seed      ║"
	@echo "║                                                      ║"
	@echo "║  DATABASE                                            ║"
	@echo "║    make db-up          Start local TimescaleDB       ║"
	@echo "║    make db-migrate     Apply public research schema  ║"
	@echo "║    make db-seed        Load deterministic pilot data ║"
	@echo "║    make db-status      Show pilot row/time coverage  ║"
	@echo "║    make db-shell       Open psql                     ║"
	@echo "║    make db-down        Stop local TimescaleDB        ║"
	@echo "║    make db-reset       Recreate local DB volume      ║"
	@echo "║                                                      ║"
	@echo "║  RESEARCH                                            ║"
	@echo "║    make demo           DB-backed pilot research run  ║"
	@echo "║    make demo-synthetic In-memory synthetic example   ║"
	@echo "║    make demo-paper     Policy-to-broker simulation    ║"
	@echo "║    make backend        Local simulation API           ║"
	@echo "║                                                      ║"
	@echo "║  QUALITY                                             ║"
	@echo "║    make test           Run tests                     ║"
	@echo "║    make coverage       Tests + coverage report      ║"
	@echo "║    make lint           Run Ruff                      ║"
	@echo "║    make audit          Dependency audit              ║"
	@echo "║    make ci             lint + test + compile + audit ║"
	@echo "╚══════════════════════════════════════════════════════╝"
	@echo ""

setup:
	@test -d .venv || python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -e ".[dev,database,backend]"

bootstrap: setup db-up db-migrate db-seed
	@$(MAKE) db-status
	@echo "Research environment ready. Run: make demo"

db-up:
	$(COMPOSE) up -d timescaledb
	@echo "Waiting for a stable TimescaleDB health state..."
	@for i in $$(seq 1 60); do \
		status=$$(docker inspect -f '{{.State.Health.Status}}' superintel-research-timescaledb 2>/dev/null || echo starting); \
		if [ "$$status" = "healthy" ]; then \
			sleep 2; \
			status=$$(docker inspect -f '{{.State.Health.Status}}' superintel-research-timescaledb 2>/dev/null || echo starting); \
			if [ "$$status" = "healthy" ]; then \
				echo "TimescaleDB ready"; exit 0; \
			fi; \
		fi; \
		sleep 1; \
	done; \
	echo "TimescaleDB did not become stably healthy"; \
	$(COMPOSE) logs --tail=100 timescaledb; \
	exit 1

db-down:
	$(COMPOSE) down --remove-orphans

db-reset:
	@echo "Resetting ONLY the local public-research Timescale volume..."
	$(COMPOSE) down -v --remove-orphans
	@$(MAKE) db-up
	@$(MAKE) db-migrate
	@$(MAKE) db-seed

db-migrate:
	@echo "Applying public research migrations..."
	@for f in $$(find db/migrations -maxdepth 1 -name '*.sql' | sort); do \
		echo "  applying $${f}"; \
		$(COMPOSE) exec -T timescaledb psql -v ON_ERROR_STOP=1 -U $(DB_USER) -d $(DB_NAME) < "$${f}"; \
	done

db-seed:
	DATABASE_URL="$(DB_URL)" $(PYTHON) scripts/seed_pilot_data.py

db-shell:
	$(COMPOSE) exec timescaledb psql -U $(DB_USER) -d $(DB_NAME)

db-status:
	@$(COMPOSE) exec -T timescaledb psql -U $(DB_USER) -d $(DB_NAME) -c \
		"SELECT symbol, count(*) AS bars, min(ts) AS first_ts, max(ts) AS last_ts FROM research.market_bars GROUP BY symbol ORDER BY symbol;"

demo: demo-db

demo-db:
	DATABASE_URL="$(DB_URL)" $(PYTHON) scripts/timescale_demo.py

demo-synthetic:
	$(PYTHON) examples/synthetic_pair_research.py

demo-paper:
	$(PYTHON) examples/paper_execution_simulation.py

backend:
	DATABASE_URL="$(DB_URL)" $(PYTHON) -m uvicorn superintel_research.backend.main:app --host 127.0.0.1 --port 8000 --reload

test:
	$(PYTHON) -m pytest -q

coverage:
	$(PYTHON) -m pytest -q --cov=superintel_research --cov-report=term-missing --cov-report=xml:coverage.xml --cov-report=html:coverage-html

lint:
	$(PYTHON) -m ruff check src tests examples scripts

audit:
	$(PYTHON) -m pip_audit

ci: lint test
	$(PYTHON) -m compileall -q src scripts
	@$(MAKE) audit

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
