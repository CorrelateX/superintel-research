"""Public boundary between proprietary alpha and generic trade simulation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class TradeAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class MarketSnapshot:
    """Minimal point-in-time input supplied to a trading policy."""

    symbol: str
    price: float
    score: float


@dataclass(frozen=True)
class TradeIntent:
    """Broker-neutral action proposed by a policy."""

    symbol: str
    action: TradeAction
    quantity: float
    reference_price: float


class TradingPolicy(Protocol):
    """Contract implemented privately by real alpha policies."""

    def decide(
        self,
        snapshot: MarketSnapshot,
        *,
        current_quantity: float,
    ) -> TradeIntent | None:
        """Return an intent using only information available at the snapshot."""
        ...