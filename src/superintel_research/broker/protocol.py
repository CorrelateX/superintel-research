"""Abstract broker adapter protocol for server/credential-agnostic execution."""

from __future__ import annotations

from typing import Protocol

from superintel_research.broker.models import (
    AccountSummary,
    OrderRequest,
    OrderResult,
    Position,
)


class BrokerAdapter(Protocol):
    """Broker-neutral interface consumed by deterministic simulations."""

    def submit_order(self, request: OrderRequest, current_price: float) -> OrderResult:
        """Submit and process an order."""
        ...

    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        ...

    def get_positions(self) -> dict[str, Position]:
        """Return active open positions."""
        ...

    def get_account_summary(self) -> AccountSummary:
        """Return account balance and equity summary."""
        ...

    def get_orders(self) -> list[OrderResult]:
        """Return order history."""
        ...
