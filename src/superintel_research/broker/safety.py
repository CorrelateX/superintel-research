"""Production execution safety guards and kill-switch checks."""

from __future__ import annotations

import os
from dataclasses import dataclass

from superintel_research.broker.models import OrderRequest


class SafetyViolationError(RuntimeError):
    """Raised when an order violates execution safety guards."""


@dataclass
class KillSwitchGuard:
    """Master trading safety guard checking environment flags and risk limits."""

    max_notional_usd: float = 10_000.0
    max_order_quantity: float = 100_000.0

    def is_kill_switch_active(self) -> bool:
        flag = os.environ.get("KILL_SWITCH", "0").lower()
        return flag in {"1", "true", "yes", "on"}

    def validate_order(self, request: OrderRequest, reference_price: float) -> None:
        if self.is_kill_switch_active():
            raise SafetyViolationError("Execution halted: Master KILL_SWITCH is ACTIVE")

        if request.quantity <= 0:
            raise SafetyViolationError(f"Invalid order quantity: {request.quantity}")

        if request.quantity > self.max_order_quantity:
            raise SafetyViolationError(
                f"Order quantity {request.quantity} exceeds max limit {self.max_order_quantity}"
            )

        notional = request.quantity * reference_price
        if notional > self.max_notional_usd:
            raise SafetyViolationError(
                f"Order notional ${notional:,.2f} exceeds max limit ${self.max_notional_usd:,.2f}"
            )
