# Public research database

This directory contains the deliberately small TimescaleDB surface exposed by the public research extract.

## Scope

The public schema contains only observed OHLCV bars:

```text
research.market_bars
├── ts
├── symbol
├── open
├── high
├── low
├── close
├── volume
└── source
```

It exists to demonstrate reproducible time-series storage, bounded temporal queries, stable data contracts, and integration with the public statistical pipeline.

It does **not** reproduce the private SuperIntel database. Private feature stores, research scores, candidate rankings, signals, portfolio state, execution records, provider metadata, model state, and operational tables are intentionally absent.

## Quick start

```bash
make bootstrap
make demo
```

`make bootstrap` starts a localhost-only TimescaleDB container, applies the public migrations, and seeds deterministic synthetic pilot data. The seed is intentionally small and is not market data.

## Bring your own data

The included pilot seed is only a reproducibility fixture. Users can populate `research.market_bars` with their own lawful historical data while keeping the same storage interface and statistical pipeline.

The public code intentionally does not prescribe a data vendor, symbol universe, ingestion policy, or proprietary research configuration.
