from __future__ import annotations

from fastapi.testclient import TestClient
from superintel_research.backend.main import app

client = TestClient(app)


def test_research_console_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "SuperIntel Research Console" in response.text


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "kill_switch_active" in data


def test_broker_account_summary():
    response = client.get("/api/v1/simulation/account")
    assert response.status_code == 200
    data = response.json()
    assert data["currency"] == "USD"
    assert data["cash_balance"] == 100_000.0


def test_submit_paper_order():
    payload = {
        "symbol": "SPY",
        "side": "BUY",
        "quantity": 10.0,
        "current_price": 500.0,
    }
    response = client.post("/api/v1/simulation/order", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "FILLED"
    assert data["symbol"] == "SPY"


def test_kill_switch_toggle():
    # Engaged
    res = client.post("/api/v1/simulation/safety/kill-switch", json={"active": True})
    assert res.status_code == 200
    assert res.json()["kill_switch_active"] is True

    # Check order rejected
    payload = {
        "symbol": "SPY",
        "side": "BUY",
        "quantity": 5.0,
        "current_price": 500.0,
    }
    order_res = client.post("/api/v1/simulation/order", json=payload)
    assert order_res.json()["status"] == "REJECTED"

    # Disengaged
    res = client.post("/api/v1/simulation/safety/kill-switch", json={"active": False})
    assert res.status_code == 200
    assert res.json()["kill_switch_active"] is False
