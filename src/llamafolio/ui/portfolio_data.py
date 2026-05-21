"""Sync helpers to fetch portfolio state for the Streamlit sidebar.

We use the sync alpaca-py SDK here (not the MCP path) because the sidebar just
needs a quick read on every rerun — the MCP server is reserved for the agents.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import yfinance as yf
from alpaca.trading.client import TradingClient

from llamafolio.config import Settings


@dataclass
class AccountSnapshot:
    equity: float
    cash: float
    buying_power: float
    invested: float
    cash_pct: float


@dataclass
class PositionRow:
    symbol: str
    qty: float
    avg_entry: float
    current: float
    market_value: float
    weight_pct: float
    plpc: float
    sector: str


def _client(settings: Settings) -> TradingClient:
    return TradingClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
        paper=True,
    )


@lru_cache(maxsize=64)
def _sector_of(symbol: str) -> str:
    try:
        info = yf.Ticker(symbol).info
        return info.get("sector") or "Unknown"
    except Exception:  # noqa: BLE001
        return "Unknown"


def load_account(settings: Settings) -> AccountSnapshot:
    a = _client(settings).get_account()
    equity = float(a.portfolio_value)
    cash = float(a.cash)
    invested = max(equity - cash, 0.0)
    return AccountSnapshot(
        equity=equity,
        cash=cash,
        buying_power=float(a.buying_power),
        invested=invested,
        cash_pct=(cash / equity * 100) if equity else 0.0,
    )


def load_positions(settings: Settings) -> list[PositionRow]:
    client = _client(settings)
    raw = client.get_all_positions()
    if not raw:
        return []
    total = sum(float(p.market_value) for p in raw)
    rows: list[PositionRow] = []
    for p in raw:
        mv = float(p.market_value)
        rows.append(
            PositionRow(
                symbol=p.symbol,
                qty=float(p.qty),
                avg_entry=float(p.avg_entry_price),
                current=float(p.current_price),
                market_value=mv,
                weight_pct=(mv / total * 100) if total else 0.0,
                plpc=float(p.unrealized_plpc) * 100,
                sector=_sector_of(p.symbol),
            )
        )
    rows.sort(key=lambda r: r.market_value, reverse=True)
    return rows


def sector_breakdown(positions: list[PositionRow]) -> dict[str, float]:
    """Return {sector: weight_pct} aggregated from positions."""
    out: dict[str, float] = {}
    for p in positions:
        out[p.sector] = out.get(p.sector, 0.0) + p.weight_pct
    return dict(sorted(out.items(), key=lambda kv: kv[1], reverse=True))
