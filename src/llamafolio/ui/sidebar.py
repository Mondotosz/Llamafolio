"""Left-rail portfolio dashboard.

Reads the account, positions and intraday equity history from the data
layer once per Streamlit run, then renders:

  - hero equity card with intraday P/L delta,
  - intraday equity sparkline (when at least two points are available),
  - Cash + Invested mini metrics,
  - position cards sorted by market value,
  - sector exposure donut,
  - 'Refresh data' button.

If Alpaca can't be reached the rail shows a single error message and
returns early — the rest of the app stays usable for offline browsing.
"""
from __future__ import annotations

import streamlit as st

from llamafolio.config import load_settings
from llamafolio.data import (
    AccountSnapshot,
    EquityHistory,
    PositionRow,
    load_account,
    load_equity_history,
    load_positions,
    sector_breakdown,
)
from llamafolio.ui.charts import equity_sparkline, sector_donut


def _hero_metric(label: str, value: str, delta: str | None = None) -> str:
    delta_html = f"<div class='lf-hero-delta'>{delta}</div>" if delta else ""
    return (
        f"<div class='lf-hero'>"
        f"<div class='lf-hero-label'>{label}</div>"
        f"<div class='lf-hero-value'>{value}</div>"
        f"{delta_html}</div>"
    )


def _mini_metric(label: str, value: str, delta: str | None = None) -> str:
    delta_html = f"<div class='lf-metric-mini-delta'>{delta}</div>" if delta else ""
    return (
        f"<div class='lf-metric-mini'>"
        f"<div class='lf-metric-mini-label'>{label}</div>"
        f"<div class='lf-metric-mini-value'>{value}</div>"
        f"{delta_html}</div>"
    )


def _position_card(p: PositionRow) -> str:
    pl_cls = "gain-pill" if p.plpc >= 0 else "loss-pill"
    pl_sign = "+" if p.plpc >= 0 else ""
    return (
        f"<div class='lf-pos'>"
        f"<div><div class='lf-pos-sym'>{p.symbol}</div>"
        f"<div class='lf-pos-meta'>{p.sector}</div></div>"
        f"<div><div class='lf-pos-val'>${p.market_value:,.0f}</div>"
        f"<div class='lf-pos-pl'>"
        f"<span class='{pl_cls}'>{pl_sign}{p.plpc:.2f}%</span> "
        f"&middot; {p.weight_pct:.0f}%"
        f"</div></div>"
        f"</div>"
    )


def _intraday_pl_delta(history: EquityHistory | None) -> str | None:
    if history is None or not history.base_value:
        return None
    sign = "+" if history.pnl >= 0 else ""
    cls = "gain" if history.pnl >= 0 else "loss"
    return (
        f"<span class='{cls}'>{sign}${history.pnl:,.0f} "
        f"({sign}{history.pnl_pct:.2f}%)</span>"
        " <span style='color:var(--text-dim);'>· Today</span>"
    )


def render() -> None:
    """Render the sidebar — Alpaca state + interactive controls."""
    settings = load_settings()
    with st.sidebar:
        try:
            account: AccountSnapshot = load_account(settings)
            positions: list[PositionRow] = load_positions(settings)
            history = load_equity_history(settings, period="1D", timeframe="1Min")
        except Exception as e:  # noqa: BLE001
            st.error(f"Failed to load Alpaca account: {e}")
            return

        # Hero metric with intraday delta + sparkline
        st.markdown(
            _hero_metric(
                "Total equity",
                f"${account.equity:,.0f}",
                _intraday_pl_delta(history),
            ),
            unsafe_allow_html=True,
        )
        if history and len(history.equity) > 1:
            st.plotly_chart(
                equity_sparkline(history),
                width="stretch",
                config={"displayModeBar": False},
            )

        # Cash + Invested mini metrics side-by-side
        c1, c2 = st.columns(2)
        c1.markdown(
            _mini_metric(
                "Cash",
                f"${account.cash:,.0f}",
                f"{account.cash_pct:.0f}% of equity",
            ),
            unsafe_allow_html=True,
        )
        c2.markdown(
            _mini_metric("Invested", f"${account.invested:,.0f}"),
            unsafe_allow_html=True,
        )

        # Positions block
        st.markdown(
            f"<div class='lf-section'>Positions &middot; {len(positions)}</div>",
            unsafe_allow_html=True,
        )
        if not positions:
            st.markdown(
                "<div class='lf-pos' style='justify-content:center;"
                "text-align:center;color:var(--text-muted);'>"
                "No open positions yet.</div>",
                unsafe_allow_html=True,
            )
        else:
            for p in positions:
                st.markdown(_position_card(p), unsafe_allow_html=True)
            st.markdown(
                "<div class='lf-section'>Sector exposure</div>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                sector_donut(sector_breakdown(positions)),
                width="stretch",
                config={"displayModeBar": False},
            )

        st.markdown("<div class='lf-section'>&nbsp;</div>", unsafe_allow_html=True)
        if st.button("Refresh data", width="stretch"):
            st.rerun()
