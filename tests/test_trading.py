from __future__ import annotations

from superintel_research.broker.models import OrderRequest, OrderSide, OrderStatus
from superintel_research.broker.paper_broker import PaperBrokerAdapter
from superintel_research.trading.protocol import MarketSnapshot, TradeAction
from superintel_research.trading.toy_policy import ToyThresholdPolicy


def test_toy_policy_enters_and_exits_long_position() -> None:
    policy = ToyThresholdPolicy(quantity=10.0)

    entry = policy.decide(
        MarketSnapshot("SYNTH_A", 100.0, -2.5),
        current_quantity=0.0,
    )
    exit_intent = policy.decide(
        MarketSnapshot("SYNTH_A", 102.0, 0.1),
        current_quantity=10.0,
    )

    assert entry is not None and entry.action == TradeAction.BUY
    assert exit_intent is not None and exit_intent.action == TradeAction.SELL
    assert exit_intent.quantity == 10.0


def test_policy_intent_executes_through_paper_broker() -> None:
    broker = PaperBrokerAdapter(initial_cash=10_000.0)
    policy = ToyThresholdPolicy(quantity=10.0)
    snapshot = MarketSnapshot("SYNTH_A", 100.0, -2.5)

    intent = policy.decide(snapshot, current_quantity=0.0)
    assert intent is not None
    result = broker.submit_order(
        OrderRequest(
            symbol=intent.symbol,
            side=OrderSide(intent.action.value),
            quantity=intent.quantity,
        ),
        current_price=intent.reference_price,
    )

    assert result.status == OrderStatus.FILLED
    assert broker.get_positions()["SYNTH_A"].quantity == 10.0
