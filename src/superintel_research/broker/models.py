"""Data models for credential-agnostic broker layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class OrderRequest:
    """Request to submit an order."""

    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType = OrderType.MARKET
    price: float | None = None
    client_order_id: str | None = None


@dataclass
class OrderResult:
    """Result of an order lifecycle."""

    order_id: str
    client_order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    filled_quantity: float
    avg_fill_price: float
    status: OrderStatus
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reject_reason: str | None = None


@dataclass
class Position:
    """Portfolio position."""

    symbol: str
    quantity: float
    avg_entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float


@dataclass
class AccountSummary:
    """Broker account balance and margin metrics."""

    account_id: str
    currency: str
    cash_balance: float
    equity: float
    unrealized_pnl: float
    realized_pnl: float
    initial_cash: float
