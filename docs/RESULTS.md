# Results and Research Posture

The purpose of this repository is to demonstrate a research process that can reject weak evidence, not to manufacture a profitability story.

## What the larger research program established

The private program has exercised the full loop from market data through statistical candidate generation, dataset construction, supervised baselines, learned reranking and economic evaluation.

Early supervised experiments were approximately coin-flip at the evaluated sample size. Learned ranking improved some classification/hit-rate measures in later experiments, but the evaluated ranking arms remained economically negative after costs. Those experiments therefore did **not** establish durable alpha.

That outcome is intentionally stated rather than hidden.

## Why a negative result is useful

The work still validates several engineering capabilities:

- reproducible research datasets;
- explicit market-time semantics;
- multiple-testing control across candidate families;
- cost-aware outcome construction;
- purged temporal evaluation;
- train-only preprocessing;
- separation of classifier quality from realized economic quality;
- investigation of leakage when apparently strong model metrics conflict with economic results.

## What is not published

The public repository does not provide the private experiment's exact universe, pair list, candidate score, feature set, fusion weights, strategy thresholds, portfolio/risk parameters or live execution configuration.

As a result, this repository should be read as an engineering and methodology artifact, not as a reproducible trading strategy.
