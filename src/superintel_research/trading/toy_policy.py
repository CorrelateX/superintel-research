"""Illustrative policy for exercising the public simulation boundary."""

from __future__ import annotations

from dataclasses import dataclass

from superintel_research.trading.protocol import (
    MarketSnapshot,
    TradeAction,
    TradeIntent,
)


@dataclass(frozen=True)
class ToyThresholdPolicy:
    """Long-only threshold example; defaults are not SuperIntel parameters."""

    entry_score: float = -2.0
    exit_score: float = 0.0
    quantity: float = 1.0

    def decide(
        self,
        snapshot: MarketSnapshot,
        *,
        current_quantity: float,
    ) -> TradeIntent | None:
        if snapshot.price <= 0 or self.quantity <= 0:
            raise ValueError("price and policy quantity must be positive")
        if current_quantity == 0 and snapshot.score <= self.entry_score:
            action = TradeAction.BUY
        elif current_quantity > 0 and snapshot.score >= self.exit_score:
            action = TradeAction.SELL
        else:
            return None
        return TradeIntent(
            symbol=snapshot.symbol,
            action=action,
            quantity=self.quantity if action == TradeAction.BUY else current_quantity,
            reference_price=snapshot.price,
        )