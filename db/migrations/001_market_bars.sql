CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE SCHEMA IF NOT EXISTS research;

CREATE TABLE IF NOT EXISTS research.market_bars (
    ts TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION NOT NULL DEFAULT 0,
    source TEXT NOT NULL DEFAULT 'pilot',
    PRIMARY KEY (symbol, ts),
    CHECK (high >= low),
    CHECK (open > 0),
    CHECK (high > 0),
    CHECK (low > 0),
    CHECK (close > 0),
    CHECK (volume >= 0)
);

SELECT create_hypertable(
    'research.market_bars',
    by_range('ts'),
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_market_bars_symbol_ts_desc
    ON research.market_bars (symbol, ts DESC);
