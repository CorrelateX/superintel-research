"""Paper execution broker adapter for simulated production order matching."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from superintel_research.broker.models import (
    AccountSummary,
    OrderRequest,
    OrderResult,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
)
from superintel_research.broker.safety import KillSwitchGuard, SafetyViolationError


class PaperBrokerAdapter:
    """Deterministic long-only market-order simulator with costs and safety limits."""

    def __init__(
        self,
        initial_cash: float = 100_000.0,
        fee_bps: float = 5.0,
        slippage_bps: float = 2.0,
    ) -> None:
        self.initial_cash = float(initial_cash)
        self.cash = float(initial_cash)
        self.fee_bps = float(fee_bps)
        self.slippage_bps = float(slippage_bps)
        self.realized_pnl = 0.0

        self.positions: dict[str, Position] = {}
        self.orders: list[OrderResult] = []
        self._orders_by_client_id: dict[str, OrderResult] = {}
        self.safety_guard = KillSwitchGuard()

    def submit_order(self, request: OrderRequest, current_price: float) -> OrderResult:
        if request.client_order_id in self._orders_by_client_id:
            return self._orders_by_client_id[request.client_order_id]

        order_id = "ord_" + uuid.uuid4().hex[:12]
        client_id = request.client_order_id or "cli_" + uuid.uuid4().hex[:8]

        if request.order_type != OrderType.MARKET:
            return self._reject(
                request,
                order_id,
                client_id,
                "Paper simulation supports market orders only",
            )

        if current_price <= 0:
            return self._reject(
                request,
                order_id,
                client_id,
                "Current price must be positive",
            )

        # 1. Safety Guard Check
        try:
            self.safety_guard.validate_order(request, current_price)
        except SafetyViolationError as exc:
            return self._reject(request, order_id, client_id, str(exc))

        position = self.positions.get(request.symbol)
        if request.side == OrderSide.SELL and (
            position is None or request.quantity > position.quantity
        ):
            available = 0.0 if position is None else position.quantity
            return self._reject(
                request,
                order_id,
                client_id,
                f"Insufficient position: requested {request.quantity}, available {available}",
            )

        # 2. Compute fill price with slippage
        slippage_mult = (1.0 + self.slippage_bps / 10_000.0) if request.side == OrderSide.BUY else (1.0 - self.slippage_bps / 10_000.0)
        fill_price = current_price * slippage_mult
        notional = request.quantity * fill_price
        commission = notional * (self.fee_bps / 10_000.0)

        # 3. Capital check for BUY
        if request.side == OrderSide.BUY and (notional + commission) > self.cash:
            return self._reject(
                request,
                order_id,
                client_id,
                f"Insufficient cash balance ${self.cash:,.2f} "
                f"for required ${notional + commission:,.2f}",
            )

        # 4. Execute Fill & Update Position
        self._apply_fill(request.symbol, request.side, request.quantity, fill_price, commission)

        result = OrderResult(
            order_id=order_id,
            client_order_id=client_id,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            filled_quantity=request.quantity,
            avg_fill_price=fill_price,
            status=OrderStatus.FILLED,
        )
        self.orders.append(result)
        self._orders_by_client_id[client_id] = result
        return result

    def _reject(
        self,
        request: OrderRequest,
        order_id: str,
        client_id: str,
        reason: str,
    ) -> OrderResult:
        result = OrderResult(
            order_id=order_id,
            client_order_id=client_id,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            filled_quantity=0.0,
            avg_fill_price=0.0,
            status=OrderStatus.REJECTED,
            reject_reason=reason,
        )
        self.orders.append(result)
        self._orders_by_client_id[client_id] = result
        return result

    def _apply_fill(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: float,
        commission: float,
    ) -> None:
        pos = self.positions.get(symbol, Position(symbol, 0.0, 0.0, price, 0.0, 0.0))

        if side == OrderSide.BUY:
            self.cash -= (quantity * price + commission)
            new_qty = pos.quantity + quantity
            if new_qty > 0:
                pos.avg_entry_price = (
                    (pos.quantity * pos.avg_entry_price)
                    + (quantity * price)
                    + commission
                ) / new_qty
            pos.quantity = new_qty
        else:
            self.cash += (quantity * price - commission)
            # Realized PnL calculation
            pnl = (price - pos.avg_entry_price) * min(quantity, pos.quantity) - commission
            self.realized_pnl += pnl
            pos.realized_pnl += pnl
            pos.quantity -= quantity

        pos.current_price = price
        pos.unrealized_pnl = (price - pos.avg_entry_price) * pos.quantity if pos.quantity > 0 else 0.0

        if pos.quantity <= 0:
            pos.quantity = 0.0
            pos.avg_entry_price = 0.0
            pos.unrealized_pnl = 0.0

        self.positions[symbol] = pos

    def cancel_order(self, order_id: str) -> bool:
        for order in self.orders:
            if order.order_id == order_id and order.status == OrderStatus.PENDING:
                order.status = OrderStatus.CANCELLED
                order.updated_at = datetime.now(timezone.utc)
                return True
        return False

    def get_positions(self) -> dict[str, Position]:
        return {sym: pos for sym, pos in self.positions.items() if pos.quantity > 0}

    def get_account_summary(self) -> AccountSummary:
        unrealized = sum(p.unrealized_pnl for p in self.positions.values() if p.quantity > 0)
        position_value = sum(p.quantity * p.current_price for p in self.positions.values() if p.quantity > 0)
        equity = self.cash + position_value

        return AccountSummary(
            account_id="paper_act_01",
            currency="USD",
            cash_balance=self.cash,
            equity=equity,
            unrealized_pnl=unrealized,
            realized_pnl=self.realized_pnl,
            initial_cash=self.initial_cash,
        )

    def get_orders(self) -> list[OrderResult]:
        return list(self.orders)
