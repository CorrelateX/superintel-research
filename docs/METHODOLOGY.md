# Methodology

This document describes the methodology that is intentionally public. It does not disclose the private candidate-ranking recipe, learned fusion feature set, alpha policy, strategy parameters, portfolio policy, or live execution logic.

## 1. Temporal alignment

Pair tests begin only after both legs are normalized onto canonical market observation time. The public implementation:

- resolves a market timestamp field;
- sorts observations chronologically;
- resolves duplicate timestamps deterministically;
- takes the inner intersection of actually observed timestamps;
- performs no forward fill between pair legs;
- rejects non-finite or non-positive aligned prices.

This prevents the common error of truncating two arrays to equal length and assuming row `i` means the same market instant in both.

## 2. Cointegration diagnostics

The public reference implementation exposes standard Engle–Granger mechanics:

1. deterministic OLS orientation `Y = alpha + beta * X + residual`;
2. Engle–Granger test with a constant trend and AIC lag selection;
3. ADF diagnostic on fitted residuals;
4. residual mean-reversion half-life in observation periods.

The module returns diagnostics only. It does not convert them into a proprietary candidate score or trade decision.

## 3. Multiple hypotheses

Testing many pairs inflates false discoveries. The public `multiple_testing.py` implements the Benjamini–Hochberg step-up procedure and keeps a deterministic family identity based on statistical configuration.

FDR control is treated as an eligibility/diagnostic layer, not as a hidden bonus added to a ranking score.

## 4. Point-in-time labels

The generic public label builder produces forward-return outcomes with explicit round-trip costs. The feature row at `t` is conceptually separated from the outcome window `t+1 ... t+H`.

Exact private pair-entry logic and private strategy-specific label parameters are not included.

## 5. Temporal evaluation

`WalkForwardSplitter` produces chronological rolling folds with an explicit purge gap. `WalkForwardEvaluator` fits preprocessing inside each training fold and then transforms the corresponding test fold.

There is no random train/test shuffle in the temporal research path.

## 6. Reporting

Two metric families are kept separate:

- **classification:** accuracy, precision, recall, F1, ROC-AUC, PR-AUC and Brier score;
- **economic:** hit rate, mean net return, profit factor, annualized Sharpe, max drawdown and trade count.

A model can improve one family without establishing an economic edge. Public conclusions are written accordingly.

## 7. Paper simulation

The optional simulation path is intentionally separate from statistical eligibility. A policy receives a point-in-time snapshot and may emit a broker-neutral intent. The paper broker then applies inventory checks, explicit costs, idempotency and account reconciliation. The included toy policy demonstrates this contract; it is not evidence of alpha and does not represent private parameters.
