"""Plotly charts rendered in the sidebar.

Two minimal, on-theme charts:

- `equity_sparkline(history)` — small filled area chart of intraday
  equity. Green when MTD P/L >= 0, red otherwise. No axes, no legend.
- `sector_donut(breakdown)` — sector exposure donut with a slate palette
  matching the brand and a vertical legend to the right.
"""
from __future__ import annotations

import plotly.graph_objects as go

from llamafolio.data import EquityHistory


def equity_sparkline(history: EquityHistory) -> go.Figure:
    """Filled-area sparkline showing the equity curve."""
    is_gain = history.pnl >= 0
    line_color = "#047857" if is_gain else "#B91C1C"
    fill_color = "rgba(4, 120, 87, 0.10)" if is_gain else "rgba(185, 28, 28, 0.10)"
    fig = go.Figure(
        go.Scatter(
            x=history.timestamps,
            y=history.equity,
            mode="lines",
            line=dict(color=line_color, width=2),
            fill="tozeroy",
            fillcolor=fill_color,
            hovertemplate="%{x|%H:%M}<br><b>$%{y:,.0f}</b><extra></extra>",
        )
    )
    fig.update_layout(
        height=90,
        margin=dict(l=0, r=0, t=4, b=0),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(
            visible=False,
            range=[min(history.equity) * 0.999, max(history.equity) * 1.001],
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#E5E7EB",
            font=dict(color="#0F172A", size=11),
        ),
    )
    return fig


_DONUT_COLORS = (
    "#0F172A",
    "#334155",
    "#64748B",
    "#94A3B8",
    "#CBD5E1",
    "#E2E8F0",
    "#475569",
)


def sector_donut(breakdown: dict[str, float]) -> go.Figure:
    """Sector-exposure donut with the brand palette."""
    fig = go.Figure(
        go.Pie(
            labels=list(breakdown.keys()),
            values=list(breakdown.values()),
            hole=0.65,
            sort=False,
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value:.1f}%<extra></extra>",
            marker=dict(
                colors=list(_DONUT_COLORS),
                line=dict(color="#FFFFFF", width=2),
            ),
        )
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            font=dict(size=10, color="#0F172A"),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=0, r=0, t=5, b=5),
        height=190,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="ui-sans-serif, system-ui, sans-serif", color="#0F172A"),
    )
    return fig
