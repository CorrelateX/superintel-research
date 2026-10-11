# Architecture

## Public research boundary

The public extract is organized as a small Python package with six concerns:

```text
statistics/   -> temporal alignment, statistical inference, multiple-testing control
datasets/     -> point-in-time labels and purged temporal folds
evaluation/   -> classifier metrics, economic metrics and walk-forward evaluation
storage/      -> replaceable observed-market-data access
trading/      -> protocol boundary for private alpha policies
broker/       -> deterministic long-only paper execution
backend/      -> local research and simulation API
frontend/     -> same-origin diagnostics and paper-simulation console
```

The flow is intentionally one-way:

```text
raw research frame
  -> canonical event-time alignment
  -> statistical diagnostics
  -> hypothesis-family correction
  -> point-in-time dataset
  -> purged walk-forward folds
  -> model evaluation
  -> statistical + economic reporting
  -> optional TradingPolicy
  -> paper broker
  -> simulation API
  -> local console
```

## Design invariants

### Event time over array position

Two independently collected price histories are not assumed to share identical rows. `pair_alignment.py` intersects actual observation timestamps, resolves duplicates deterministically and does not forward-fill missing pair observations.

### Statistical eligibility is not ranking

Benjamini–Hochberg correction is exposed as a statistical control layer. It answers whether evidence survives a hypothesis family; it is not a public alpha score.

### Future information stays outside features

Label construction uses future observations only to construct the outcome. Temporal splits remain chronological, and purge gaps separate the training horizon from the test horizon.

### Preprocessing belongs inside a fold

The public walk-forward evaluator fits `StandardScaler` only on each fold's training sample, then applies that fitted transform to the corresponding test sample.

### Model metrics and trading metrics are separate

Classification quality and economic outcomes are intentionally different modules. The architecture prevents a classifier metric from being presented as equivalent to net profitability.

### Alpha policy is an extension point

The public `TradingPolicy` protocol defines the point where a private decision policy can emit broker-neutral intents. The included toy policy is intentionally generic and is not used by the statistical research pipeline.

### Paper execution is deliberately narrow

The public broker supports deterministic long-only market-order simulation. It rejects unsupported order types and unbacked sells, applies explicit costs, deduplicates client order IDs and reconciles realized PnL with account equity.

## Intentionally absent layers

The private system contains additional architecture for data acquisition, feature research, candidate ranking, model fusion, alpha policy, risk/portfolio policy, live execution, orchestration, authenticated product APIs, observability and deployment. Those layers are outside the public boundary.
