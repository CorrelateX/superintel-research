"""Generic point-in-time forward-return labels with an explicit cost model.

The public defaults are neutral examples, not private strategy parameters.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class LabelConfig:
    """Public research label configuration.

    Costs are round-trip basis points. Optional stop/target exits are fractions
    of entry price and are evaluated only when high/low columns are available.
    """

    horizon: int = 1
    fee_bps: float = 0.0
    slippage_bps: float = 0.0
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None

    @property
    def round_trip_cost(self) -> float:
        return (self.fee_bps + self.slippage_bps) / 10_000.0


class LabelBuilder:
    """Build long-side forward-return outcomes without contaminating features."""

    def __init__(self, config: LabelConfig | None = None) -> None:
        self.config = config or LabelConfig()

    def build(self, frame: pd.DataFrame) -> pd.DataFrame:
        cfg = self.config
        if "close" not in frame:
            raise ValueError("label construction requires a 'close' column")
        if cfg.horizon < 1:
            raise ValueError("horizon must be >= 1")
        if cfg.fee_bps < 0 or cfg.slippage_bps < 0:
            raise ValueError("cost assumptions must be non-negative")

        use_exits = (
            {"high", "low"}.issubset(frame.columns)
            and (cfg.stop_loss_pct is not None or cfg.take_profit_pct is not None)
        )
        if use_exits:
            gross, exit_type = self._forward_return_with_exits(frame, cfg.horizon)
        else:
            gross = frame["close"].pct_change(cfg.horizon).shift(-cfg.horizon)
            exit_type = None

        output = pd.DataFrame(index=frame.index)
        output["forward_return"] = gross
        output["round_trip_cost"] = cfg.round_trip_cost
        output["forward_return_net"] = gross - cfg.round_trip_cost
        output["profitable_trade"] = (output["forward_return_net"] > 0).astype(int)
        if exit_type is not None:
            output["exit_type"] = exit_type

        return output.iloc[: -cfg.horizon]

    def _forward_return_with_exits(
        self,
        frame: pd.DataFrame,
        horizon: int,
    ) -> tuple[pd.Series, pd.Series]:
        cfg = self.config
        close = frame["close"]
        forward_high = pd.concat(
            [frame["high"].shift(-step) for step in range(1, horizon + 1)],
            axis=1,
        ).max(axis=1)
        forward_low = pd.concat(
            [frame["low"].shift(-step) for step in range(1, horizon + 1)],
            axis=1,
        ).min(axis=1)

        horizon_return = (close.shift(-horizon) - close) / close
        stop_hit = (
            forward_low <= close * (1 - cfg.stop_loss_pct)
            if cfg.stop_loss_pct is not None
            else pd.Series(False, index=frame.index)
        )
        target_hit = (
            forward_high >= close * (1 + cfg.take_profit_pct)
            if cfg.take_profit_pct is not None
            else pd.Series(False, index=frame.index)
        )

        result = horizon_return.copy()
        if cfg.stop_loss_pct is not None:
            result = result.where(~stop_hit, -cfg.stop_loss_pct)
        if cfg.take_profit_pct is not None:
            result = result.where(stop_hit | ~target_hit, cfg.take_profit_pct)

        exit_type = pd.Series("horizon", index=frame.index)
        if cfg.stop_loss_pct is not None:
            exit_type = exit_type.where(~stop_hit, "stop")
        if cfg.take_profit_pct is not None:
            exit_type = exit_type.where(stop_hit | ~target_hit, "target")
        return result, exit_type
