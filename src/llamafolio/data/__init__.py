"""Pure data-access layer.

Sync helpers around the Alpaca SDK and yfinance for everything the host
needs to know about the user's portfolio before kicking off an agent
turn. No Streamlit, no Plotly, no LangChain — those imports belong to
the upper layers (`llamafolio.ui` and `llamafolio.agents`).
"""
from llamafolio.data.portfolio import (
    AccountSnapshot,
    EquityHistory,
    PositionRow,
    load_account,
    load_equity_history,
    load_positions,
    render_portfolio_context,
    sector_breakdown,
)

__all__ = [
    "AccountSnapshot",
    "EquityHistory",
    "PositionRow",
    "load_account",
    "load_equity_history",
    "load_positions",
    "render_portfolio_context",
    "sector_breakdown",
]
