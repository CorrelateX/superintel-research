# Public / Private Boundary

This repository is a curated research-engineering extract. The omission of some layers is deliberate intellectual-property and operational-security policy, not an indication that the private system ends at this repository boundary.

## Public

The following classes of work are intentionally shown:

- canonical event-time alignment;
- generic statistical tests and residual diagnostics;
- Benjamini–Hochberg multiple-testing correction;
- point-in-time dataset construction patterns;
- purge-gap temporal splitting;
- train-only preprocessing inside walk-forward evaluation;
- classification and economic evaluation metrics;
- a minimal `MarketDataStore` abstraction;
- a localhost-only TimescaleDB example containing generic OHLCV bars only;
- a broker-neutral `TradingPolicy` extension contract;
- an explicitly illustrative long-only threshold policy;
- a deterministic paper broker with inventory, cost and idempotency checks;
- a localhost research and paper-simulation API;
- a same-origin console for diagnostics and paper simulation;
- deterministic synthetic pilot data and fail-closed CI.

The public database is deliberately narrow: `research.market_bars` demonstrates time-series persistence and retrieval without exposing the private SuperIntel data model.

## Withheld

The following are intentionally excluded from the public tree:

- production/provider/broker credentials and credential-validation state;
- private market datasets, pair universes and generated research state;
- the private database schema beyond the generic public OHLCV contract;
- private feature-store tables, research scores, candidate state and model state;
- live data-acquisition and live broker adapters;
- proprietary candidate screening, ranking and scoring logic;
- private engineered feature sets and learned fusion implementation;
- proprietary alpha policies, strategy thresholds and signal adapters;
- position sizing, portfolio allocation and risk policy;
- live execution, order routing and broker reconciliation;
- API authentication and private service wiring;
- agent/LLM orchestration and provider chains;
- schedulers, workers and operational automation;
- cloud/deployment topology, staging/production workflows and runbooks;
- private observability, metrics snapshots and incident/operations material;
- private product frontend and operational cockpit code.

## Configuration policy

Only illustrative research configuration is published. The local database credentials and synthetic data are disposable development defaults, not private system credentials or production parameters.

The public Makefile covers reproducible research and deterministic paper simulation. Production deployment, live execution, broker connectivity, orchestration, providers and private pipeline targets are intentionally absent.

## Security rule

No `.env`, secret, credential state, runtime state, private dataset, model artifact or generated codebase index belongs in this repository. `.gitignore` encodes that policy and CI is intentionally scoped to the public research package.
