const endpoints = {
  health: "/health",
  pairs: "/api/v1/research/pairs",
  account: "/api/v1/simulation/account",
  positions: "/api/v1/simulation/positions",
  orders: "/api/v1/simulation/orders",
  order: "/api/v1/simulation/order",
  killSwitch: "/api/v1/simulation/safety/kill-switch",
};

const byId = (id) => document.getElementById(id);
const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
const number = new Intl.NumberFormat("en-US", { maximumFractionDigits: 4 });
let killSwitchActive = false;

async function request(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `Request failed (${response.status})`);
  }
  return response.json();
}

function formatMetric(value, digits = 6) {
  return Number.isFinite(value) ? value.toFixed(digits) : "--";
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  })[character]);
}

function setPnl(element, value) {
  element.textContent = money.format(value || 0);
  element.classList.toggle("positive", value > 0);
  element.classList.toggle("negative", value < 0);
}

function renderHealth(health) {
  byId("api-status").textContent = health.status === "healthy" ? "API HEALTHY" : "API DEGRADED";
  byId("api-dot").className = `status-dot ${health.status === "healthy" ? "ok" : "error"}`;
  byId("db-status").textContent = `DB ${String(health.database).toUpperCase()}`;
  killSwitchActive = Boolean(health.kill_switch_active);
  renderKillSwitch();
}

function renderAccount(account) {
  byId("account-id").textContent = account.account_id;
  byId("equity").textContent = money.format(account.equity);
  byId("cash").textContent = money.format(account.cash_balance);
  setPnl(byId("realized-pnl"), account.realized_pnl);
}

function renderPairs(payload) {
  const rows = payload.pairs || [];
  const discoveries = rows.filter((pair) => pair.fdr_significant_05).length;
  byId("fdr-count").textContent = `${discoveries} / ${rows.length}`;
  byId("pairs-body").innerHTML = rows.length ? rows.map((pair) => `
    <tr>
      <td><strong>${escapeHtml(pair.pair_id)}</strong></td>
      <td>${number.format(pair.aligned_observations)}</td>
      <td>${formatMetric(pair.p_value)}</td>
      <td>${formatMetric(pair.q_value)}</td>
      <td>${Number.isFinite(pair.half_life_periods) ? `${number.format(pair.half_life_periods)} periods` : "--"}</td>
      <td>${formatMetric(pair.hedge_ratio, 4)}</td>
      <td><span class="decision ${pair.fdr_significant_05 ? "pass" : "review"}">${pair.fdr_significant_05 ? "PASS" : "REVIEW"}</span></td>
    </tr>`).join("") : '<tr><td colspan="7" class="empty">No eligible pair diagnostics</td></tr>';
}

function renderPositions(payload) {
  const positions = payload.positions || [];
  byId("position-count").textContent = String(positions.length);
  byId("positions-body").innerHTML = positions.length ? positions.map((position) => `
    <tr>
      <td><strong>${escapeHtml(position.symbol)}</strong></td>
      <td>${number.format(position.quantity)}</td>
      <td>${money.format(position.avg_entry_price)}</td>
      <td>${money.format(position.current_price)}</td>
      <td class="${position.unrealized_pnl >= 0 ? "buy" : "sell"}">${money.format(position.unrealized_pnl)}</td>
    </tr>`).join("") : '<tr><td colspan="5" class="empty">No open positions</td></tr>';
}

function renderOrders(payload) {
  const orders = payload.orders || [];
  byId("order-count").textContent = String(orders.length);
  byId("orders-body").innerHTML = orders.length ? orders.slice(0, 12).map((order) => `
    <tr>
      <td>${new Date(order.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</td>
      <td><strong>${escapeHtml(order.symbol)}</strong></td>
      <td class="${order.side === "BUY" ? "buy" : "sell"}">${order.side}</td>
      <td>${number.format(order.quantity)}</td>
      <td>${order.filled_quantity ? money.format(order.avg_fill_price) : "--"}</td>
      <td><span class="decision order-status ${order.status.toLowerCase()}">${order.status}</span></td>
    </tr>`).join("") : '<tr><td colspan="6" class="empty">No orders submitted</td></tr>';
}

function renderKillSwitch() {
  const button = byId("kill-switch");
  button.classList.toggle("active", killSwitchActive);
  button.setAttribute("aria-pressed", String(killSwitchActive));
  button.querySelector("span").textContent = killSwitchActive ? "RESUME SIMULATION" : "HALT SIMULATION";
}

async function refreshAll() {
  byId("refresh-all").disabled = true;
  try {
    const [health, pairs, account, positions, orders] = await Promise.all([
      request(endpoints.health), request(endpoints.pairs), request(endpoints.account),
      request(endpoints.positions), request(endpoints.orders),
    ]);
    renderHealth(health);
    renderPairs(pairs);
    renderAccount(account);
    renderPositions(positions);
    renderOrders(orders);
    byId("last-updated").textContent = `SYNC ${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}`;
  } catch (error) {
    byId("api-dot").className = "status-dot error";
    byId("api-status").textContent = "API ERROR";
    byId("order-status").textContent = error.message;
    byId("order-status").className = "form-status error";
  } finally {
    byId("refresh-all").disabled = false;
    window.lucide?.createIcons();
  }
}

byId("refresh-all").addEventListener("click", refreshAll);
byId("kill-switch").addEventListener("click", async () => {
  try {
    const result = await request(endpoints.killSwitch, {
      method: "POST",
      body: JSON.stringify({ active: !killSwitchActive }),
    });
    killSwitchActive = result.kill_switch_active;
    renderKillSwitch();
  } catch (error) {
    byId("order-status").textContent = error.message;
    byId("order-status").className = "form-status error";
  }
});

byId("order-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const submit = event.currentTarget.querySelector("button[type='submit']");
  submit.disabled = true;
  try {
    const result = await request(endpoints.order, {
      method: "POST",
      body: JSON.stringify({
        symbol: byId("order-symbol").value,
        side: document.querySelector("input[name='side']:checked").value,
        quantity: Number(byId("order-quantity").value),
        current_price: Number(byId("order-price").value),
        client_order_id: `console-${crypto.randomUUID()}`,
      }),
    });
    byId("order-status").textContent = result.status === "FILLED"
      ? `${result.side} ${number.format(result.filled_quantity)} ${result.symbol} filled at ${money.format(result.avg_fill_price)}`
      : result.reject_reason;
    byId("order-status").className = `form-status ${result.status === "FILLED" ? "success" : "error"}`;
    await refreshAll();
  } catch (error) {
    byId("order-status").textContent = error.message;
    byId("order-status").className = "form-status error";
  } finally {
    submit.disabled = false;
  }
});

window.addEventListener("DOMContentLoaded", refreshAll);