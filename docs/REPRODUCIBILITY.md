# Reproducibility

The public extract is designed to run without private services, credentials or market-data access. TimescaleDB is optional for users, but CI exercises it so the database-backed path is continuously verified.

## Environment

- Python 3.12+
- Docker + Docker Compose for the optional Timescale path
- GNU Make (or a compatible `make` implementation)
- dependencies declared in `pyproject.toml`
- deterministic synthetic pilot data
- no Redis, broker, LLM, cloud account or private database dependency

## Data provenance

All pilot bars are generated synthetically at seed time; nothing in `research.market_bars` is real market data. The four `SYNTH_*` symbols are deterministic fixtures, not market quotes.

`holiday_data/exchange_holidays.csv` is a small illustrative subset of exchange-published holiday calendars, included only so the calendar engine has something to read. Bring your own complete holiday feed for serious use.

## Canonical verification

```bash
make bootstrap
make demo
make demo-paper
make ci
```

`make bootstrap` creates the Python environment, starts the localhost-only TimescaleDB container, applies the public migration, seeds deterministic pilot bars, and reports symbol/time coverage.

`make demo` reads those bars through `TimescaleMarketDataStore` and feeds them into the public alignment, cointegration and FDR pipeline.

`make backend` serves the same-origin research console and simulation API at `http://localhost:8000/`.

For a database-free run:

```bash
make setup
make demo-synthetic
make demo-paper
make ci
```

The GitHub Actions workflow runs the fail-closed code-quality gates, measures test coverage, and additionally executes the fresh Timescale migration/seed/demo path plus the end-to-end paper-broker simulation.

## Determinism

Both public examples use fixed random seeds. The Timescale seed rewrites only rows tagged `pilot-synthetic-v1`, so repeated `make db-seed` runs are idempotent with respect to the included fixture.

Statistical results should therefore be stable for the same dependency versions and platform, subject to ordinary floating-point/library variation.

## Bring your own data

The pilot seed is intentionally small and synthetic. Users can populate `research.market_bars` with their own lawful historical OHLCV observations without modifying the statistical modules.

The public storage contract does not prescribe a data vendor, asset universe, ingestion frequency, or private research configuration.

## What cannot be reproduced from this public extract

The repository intentionally excludes private market data, private universe selection, the private database schema, proprietary ranking/fusion code, strategy parameters, portfolio/risk rules, broker execution and live operational configuration. Reproducing the private trading research from this repository alone is therefore neither expected nor intended.
