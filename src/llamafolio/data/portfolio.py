"""Sync portfolio data access.

We use the sync alpaca-py SDK here (not the MCP path) because the host
just needs a quick read before each agent turn — the MCP server is
reserved for the agents themselves. This module is intentionally free
of UI / LangChain / agentic concerns; everything it exposes is plain
dataclasses and pure functions.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache

logger = logging.getLogger(__name__)

import yfinance as yf
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetPortfolioHistoryRequest

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
                sector="Crypto" if p.asset_class.value in ("crypto", "crypto_perp") else _sector_of(p.symbol),
            )
        )
    rows.sort(key=lambda r: r.market_value, reverse=True)
    logger.info("Portfolio loaded: %d positions, total equity=$%.0f", len(rows), total)
    return rows


def sector_breakdown(positions: list[PositionRow]) -> dict[str, float]:
    """Return {sector: weight_pct} aggregated from positions."""
    out: dict[str, float] = {}
    for p in positions:
        out[p.sector] = out.get(p.sector, 0.0) + p.weight_pct
    return dict(sorted(out.items(), key=lambda kv: kv[1], reverse=True))


@dataclass
class EquityHistory:
    timestamps: list[datetime]
    equity: list[float]
    base_value: float

    @property
    def pnl(self) -> float:
        if not self.equity or not self.base_value:
            return 0.0
        return self.equity[-1] - self.base_value

    @property
    def pnl_pct(self) -> float:
        if not self.base_value:
            return 0.0
        return self.pnl / self.base_value * 100


def load_equity_history(
    settings: Settings,
    period: str = "1M",
    timeframe: str = "1D",
) -> EquityHistory | None:
    """Return the account's equity curve.

    Returns None if Alpaca rejects the request (e.g. fresh account with no
    history yet) — the caller decides what to show.
    """
    client = _client(settings)
    try:
        hist = client.get_portfolio_history(
            GetPortfolioHistoryRequest(period=period, timeframe=timeframe)
        )
    except Exception:  # noqa: BLE001
        logger.warning("Could not load equity history from Alpaca (period=%s timeframe=%s)", period, timeframe)
        return None
    if not hist.equity or not hist.timestamp:
        return None
    # Drop leading None values that Alpaca returns for sessions where no
    # snapshot was taken yet.
    equity = [e for e in hist.equity if e is not None]
    timestamps = [
        datetime.fromtimestamp(t, tz=timezone.utc)
        for t, e in zip(hist.timestamp, hist.equity)
        if e is not None
    ]
    if not equity:
        return None
    return EquityHistory(
        timestamps=timestamps,
        equity=equity,
        base_value=float(hist.base_value or equity[0]),
    )


def render_portfolio_context(
    account: AccountSnapshot,
    positions: list[PositionRow],
    history: EquityHistory | None = None,
) -> str:
    """Compact markdown context block that the supervisor / specialists can
    use *instead of* re-fetching account + positions + sectors on every turn.

    This is the core cost optimisation: a single Alpaca read on the host
    fills the LLM's context with everything the analyst would otherwise
    fetch through ~10 round-trips of MCP tool calls.
    """
    sectors = sector_breakdown(positions)
    lines: list[str] = [
        "<portfolio_context>",
        "Auto-fetched server-side. Use this instead of querying "
        "get_account_info / get_all_positions / get_fundamentals unless you "
        "explicitly need a value that is not in the table below.",
        "",
        f"Total equity: ${account.equity:,.0f}",
        f"Cash: ${account.cash:,.0f} ({account.cash_pct:.1f}% of equity)",
        f"Invested capital: ${account.invested:,.0f}",
    ]
    if history is not None and history.base_value:
        sign = "+" if history.pnl >= 0 else ""
        lines.append(
            f"Day P/L: {sign}${history.pnl:,.0f} ({sign}{history.pnl_pct:.2f}%)"
        )
    lines += ["", "Positions:"]
    if not positions:
        lines.append("- (no open positions)")
    else:
        lines.append("| Symbol | Value | % invested | Sector | P/L |")
        lines.append("|---|---|---|---|---|")
        for p in positions:
            sign = "+" if p.plpc >= 0 else ""
            lines.append(
                f"| {p.symbol} | ${p.market_value:,.0f} | {p.weight_pct:.1f}% | "
                f"{p.sector} | {sign}{p.plpc:.2f}% |"
            )
        lines += ["", "Sector exposure (of invested capital):"]
        invested = sum(p.market_value for p in positions) or 1.0
        for sector, raw_weight_pct in sectors.items():
            # sectors() returns weight as % of invested already (sum=100).
            lines.append(f"- {sector}: {raw_weight_pct:.1f}%")
    lines.append("</portfolio_context>")
    return "\n".join(lines)
