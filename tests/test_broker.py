from __future__ import annotations

import pytest

from superintel_research.broker.models import OrderRequest, OrderSide, OrderStatus, OrderType
from superintel_research.broker.paper_broker import PaperBrokerAdapter
from superintel_research.broker.safety import KillSwitchGuard, SafetyViolationError


def test_paper_broker_fills_market_order() -> None:
    broker = PaperBrokerAdapter(initial_cash=100_000.0)
    request = OrderRequest(symbol="SPY", side=OrderSide.BUY, quantity=10.0)

    result = broker.submit_order(request, current_price=500.0)

    assert result.status == OrderStatus.FILLED
    assert result.filled_quantity == 10.0
    assert result.avg_fill_price > 500.0  # Includes slippage

    positions = broker.get_positions()
    assert "SPY" in positions
    assert positions["SPY"].quantity == 10.0

    summary = broker.get_account_summary()
    assert summary.cash_balance < 100_000.0


def test_kill_switch_blocks_order(monkeypatch) -> None:
    monkeypatch.setenv("KILL_SWITCH", "1")
    broker = PaperBrokerAdapter(initial_cash=100_000.0)
    request = OrderRequest(symbol="SPY", side=OrderSide.BUY, quantity=10.0)

    result = broker.submit_order(request, current_price=500.0)
    assert result.status == OrderStatus.REJECTED
    assert "KILL_SWITCH is ACTIVE" in (result.reject_reason or "")


def test_order_exceeds_notional_limit() -> None:
    guard = KillSwitchGuard(max_notional_usd=10_000.0)
    request = OrderRequest(symbol="SPY", side=OrderSide.BUY, quantity=100.0)

    with pytest.raises(SafetyViolationError, match="exceeds max limit"):
        guard.validate_order(request, reference_price=500.0)


def test_default_notional_limit_accepts_boundary_and_rejects_above(monkeypatch) -> None:
    monkeypatch.delenv("KILL_SWITCH", raising=False)
    guard = KillSwitchGuard()
    assert guard.max_notional_usd == 10_000.0

    guard.validate_order(
        OrderRequest(symbol="SYNTH_A", side=OrderSide.BUY, quantity=100.0),
        reference_price=100.0,
    )
    with pytest.raises(SafetyViolationError, match="Order notional .* exceeds max limit"):
        guard.validate_order(
            OrderRequest(symbol="SYNTH_A", side=OrderSide.BUY, quantity=101.0),
            reference_price=100.0,
        )


def test_paper_broker_enforces_default_notional_limit(monkeypatch) -> None:
    monkeypatch.delenv("KILL_SWITCH", raising=False)
    broker = PaperBrokerAdapter(initial_cash=100_000.0)
    result = broker.submit_order(
        OrderRequest(symbol="SYNTH_A", side=OrderSide.BUY, quantity=101.0),
        current_price=100.0,
    )

    assert result.status == OrderStatus.REJECTED
    assert "exceeds max limit" in (result.reject_reason or "")
    assert broker.get_positions() == {}
    assert broker.get_account_summary().cash_balance == 100_000.0


def test_paper_broker_rejects_sell_without_inventory() -> None:
    broker = PaperBrokerAdapter(initial_cash=100_000.0, fee_bps=0.0, slippage_bps=0.0)

    result = broker.submit_order(
        OrderRequest(symbol="SPY", side=OrderSide.SELL, quantity=10.0),
        current_price=500.0,
    )

    assert result.status == OrderStatus.REJECTED
    assert result.reject_reason == "Insufficient position: requested 10.0, available 0.0"
    assert broker.get_account_summary().equity == 100_000.0


def test_paper_broker_deduplicates_client_order_id() -> None:
    broker = PaperBrokerAdapter(initial_cash=100_000.0)
    request = OrderRequest(
        symbol="SPY",
        side=OrderSide.BUY,
        quantity=10.0,
        client_order_id="research-run-1-order-1",
    )

    first = broker.submit_order(request, current_price=500.0)
    second = broker.submit_order(request, current_price=500.0)

    assert second is first
    assert broker.get_positions()["SPY"].quantity == 10.0
    assert len(broker.get_orders()) == 1


def test_paper_broker_rejects_limit_orders() -> None:
    broker = PaperBrokerAdapter(initial_cash=100_000.0)
    request = OrderRequest(
        symbol="SPY",
        side=OrderSide.BUY,
        quantity=10.0,
        order_type=OrderType.LIMIT,
        price=490.0,
    )

    result = broker.submit_order(request, current_price=500.0)

    assert result.status == OrderStatus.REJECTED
    assert result.reject_reason == "Paper simulation supports market orders only"


def test_round_trip_realized_pnl_reconciles_with_equity() -> None:
    broker = PaperBrokerAdapter(initial_cash=10_000.0, fee_bps=1.0, slippage_bps=1.0)
    broker.submit_order(
        OrderRequest(symbol="SYNTH_A", side=OrderSide.BUY, quantity=10.0),
        current_price=100.0,
    )
    broker.submit_order(
        OrderRequest(symbol="SYNTH_A", side=OrderSide.SELL, quantity=10.0),
        current_price=102.0,
    )

    summary = broker.get_account_summary()

    assert summary.realized_pnl == pytest.approx(summary.equity - summary.initial_cash)
