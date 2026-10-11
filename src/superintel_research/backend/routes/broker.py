"""Paper broker order and position API endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from superintel_research.broker.models import OrderRequest, OrderSide, OrderType
from superintel_research.broker.paper_broker import PaperBrokerAdapter

router = APIRouter(prefix="/api/v1/simulation", tags=["Paper Simulation"])

global_paper_broker = PaperBrokerAdapter(initial_cash=100_000.0)


class OrderSubmissionBody(BaseModel):
    symbol: str = Field(..., json_schema_extra={"example": "SYNTH_A"})
    side: OrderSide = Field(..., json_schema_extra={"example": "BUY"})
    quantity: float = Field(..., gt=0, json_schema_extra={"example": 10.0})
    current_price: float = Field(..., gt=0, json_schema_extra={"example": 500.0})
    client_order_id: str | None = Field(None, json_schema_extra={"example": "cli_12345"})


@router.get("/account")
def get_account_summary():
    summary = global_paper_broker.get_account_summary()
    return {
        "account_id": summary.account_id,
        "currency": summary.currency,
        "cash_balance": summary.cash_balance,
        "equity": summary.equity,
        "unrealized_pnl": summary.unrealized_pnl,
        "realized_pnl": summary.realized_pnl,
        "initial_cash": summary.initial_cash,
    }


@router.get("/positions")
def get_positions():
    positions = global_paper_broker.get_positions()
    return {
        "positions": [
            {
                "symbol": p.symbol,
                "quantity": p.quantity,
                "avg_entry_price": p.avg_entry_price,
                "current_price": p.current_price,
                "unrealized_pnl": p.unrealized_pnl,
                "realized_pnl": p.realized_pnl,
            }
            for p in positions.values()
        ]
    }


@router.get("/orders")
def get_orders():
    orders = global_paper_broker.get_orders()
    return {
        "orders": [
            {
                "order_id": o.order_id,
                "client_order_id": o.client_order_id,
                "symbol": o.symbol,
                "side": o.side.value,
                "quantity": o.quantity,
                "filled_quantity": o.filled_quantity,
                "avg_fill_price": o.avg_fill_price,
                "status": o.status.value,
                "created_at": o.created_at.isoformat(),
                "reject_reason": o.reject_reason,
            }
            for o in reversed(orders)
        ]
    }


@router.post("/order")
def submit_order(body: OrderSubmissionBody):
    request = OrderRequest(
        symbol=body.symbol,
        side=body.side,
        quantity=body.quantity,
        order_type=OrderType.MARKET,
        client_order_id=body.client_order_id,
    )
    result = global_paper_broker.submit_order(request, current_price=body.current_price)
    return {
        "order_id": result.order_id,
        "client_order_id": result.client_order_id,
        "symbol": result.symbol,
        "side": result.side.value,
        "quantity": result.quantity,
        "filled_quantity": result.filled_quantity,
        "avg_fill_price": result.avg_fill_price,
        "status": result.status.value,
        "reject_reason": result.reject_reason,
    }
