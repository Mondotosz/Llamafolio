"""yfinance-based tools for fundamentals — what Alpaca MCP doesn't expose.

We keep returns compact (small dicts, JSON-serialisable) so they don't blow up
the LLM context window.
"""
from __future__ import annotations

from typing import Any

import yfinance as yf
from langchain_core.tools import tool


def _safe(d: dict[str, Any], key: str, default: Any = None) -> Any:
    v = d.get(key, default)
    return v if v not in (None, "") else default


def _ticker_info(symbol: str) -> dict[str, Any] | str:
    """Return yfinance info dict, or an error string if the symbol is unavailable."""
    try:
        info = yf.Ticker(symbol).info
    except Exception:  # noqa: BLE001
        return "Symbol not found — may be a crypto asset or delisted ticker."
    if not info.get("regularMarketPrice") and not info.get("marketCap"):
        return "No equity data — may be a crypto asset or unknown ticker."
    return info


@tool
def get_fundamentals(symbol: str) -> dict[str, Any]:
    """Get fundamental metrics for a stock (P/E, market cap, sector, dividend, beta, etc.).

    Args:
        symbol: Stock ticker, e.g. "AAPL".

    Returns a compact dict with: sector, industry, market_cap, pe_ratio, forward_pe,
    eps, dividend_yield, beta, 52w_high, 52w_low, profit_margin.
    """
    info = _ticker_info(symbol)
    if isinstance(info, str):
        return {"symbol": symbol.upper(), "error": info}
    return {
        "symbol": symbol.upper(),
        "name": _safe(info, "longName") or _safe(info, "shortName"),
        "sector": _safe(info, "sector"),
        "industry": _safe(info, "industry"),
        "market_cap": _safe(info, "marketCap"),
        "pe_ratio": _safe(info, "trailingPE"),
        "forward_pe": _safe(info, "forwardPE"),
        "eps": _safe(info, "trailingEps"),
        "dividend_yield": _safe(info, "dividendYield"),
        "beta": _safe(info, "beta"),
        "52w_high": _safe(info, "fiftyTwoWeekHigh"),
        "52w_low": _safe(info, "fiftyTwoWeekLow"),
        "profit_margin": _safe(info, "profitMargins"),
    }


@tool
def get_company_info(symbol: str) -> dict[str, Any]:
    """Get qualitative company info (description, country, employees, website).

    Args:
        symbol: Stock ticker, e.g. "AAPL".
    """
    info = _ticker_info(symbol)
    if isinstance(info, str):
        return {"symbol": symbol.upper(), "error": info}
    summary = _safe(info, "longBusinessSummary", "")
    return {
        "symbol": symbol.upper(),
        "name": _safe(info, "longName") or _safe(info, "shortName"),
        "country": _safe(info, "country"),
        "website": _safe(info, "website"),
        "employees": _safe(info, "fullTimeEmployees"),
        "summary": summary[:800] if summary else None,
    }


YFINANCE_TOOLS = [get_fundamentals, get_company_info]
