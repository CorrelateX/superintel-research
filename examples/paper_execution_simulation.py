"""Run a deterministic policy-to-paper-broker simulation."""

from superintel_research.broker.models import OrderRequest, OrderSide
from superintel_research.broker.paper_broker import PaperBrokerAdapter
from superintel_research.trading.protocol import MarketSnapshot
from superintel_research.trading.toy_policy import ToyThresholdPolicy


def main() -> None:
    broker = PaperBrokerAdapter(initial_cash=10_000.0, fee_bps=1.0, slippage_bps=1.0)
    policy = ToyThresholdPolicy(quantity=10.0)
    snapshots = [
        MarketSnapshot("SYNTH_A", 100.0, -2.5),
        MarketSnapshot("SYNTH_A", 101.0, -0.8),
        MarketSnapshot("SYNTH_A", 102.0, 0.2),
    ]

    for index, snapshot in enumerate(snapshots, start=1):
        position = broker.get_positions().get(snapshot.symbol)
        current_quantity = 0.0 if position is None else position.quantity
        intent = policy.decide(snapshot, current_quantity=current_quantity)
        if intent is None:
            continue
        result = broker.submit_order(
            OrderRequest(
                symbol=intent.symbol,
                side=OrderSide(intent.action.value),
                quantity=intent.quantity,
                client_order_id=f"toy-run-{index}",
            ),
            current_price=intent.reference_price,
        )
        print(
            f"{result.side.value:4s} {result.filled_quantity:5.1f} "
            f"{result.symbol} @ {result.avg_fill_price:.4f} [{result.status.value}]"
        )

    summary = broker.get_account_summary()
    print(f"ending_equity={summary.equity:.2f} realized_pnl={summary.realized_pnl:.2f}")


if __name__ == "__main__":
    main()