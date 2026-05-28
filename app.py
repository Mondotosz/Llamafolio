"""Llamafolio — Streamlit UI.

Light, data-forward theme. No emojis. Custom CSS handles typography,
spacing, agent step timeline, trade-confirmation buttons, and the
empty-state agent capability cards.
"""
from __future__ import annotations

import asyncio
import base64
import re
import time
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from llamafolio.config import load_settings
from llamafolio.graph import build_graph
from llamafolio.ui.portfolio_data import (
    AccountSnapshot,
    EquityHistory,
    PositionRow,
    load_account,
    load_equity_history,
    load_positions,
    render_portfolio_context,
    sector_breakdown,
)

ASSETS_DIR = Path(__file__).parent / "assets"
ASSISTANT_AVATAR = str(ASSETS_DIR / "llamafolio-icon-premium.png")
USER_AVATAR = str(ASSETS_DIR / "user-avatar.svg")

st.set_page_config(
    page_title="Llamafolio",
    page_icon=str(ASSETS_DIR / "favicon-512.png"),
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def _asset_b64(name: str) -> str:
    return base64.b64encode((ASSETS_DIR / name).read_bytes()).decode()


# ----------------------------------------------------------------------------
# Async glue
# ----------------------------------------------------------------------------
def _loop() -> asyncio.AbstractEventLoop:
    if "_loop" not in st.session_state:
        st.session_state["_loop"] = asyncio.new_event_loop()
    return st.session_state["_loop"]


@st.cache_resource(show_spinner="Booting agents and Alpaca MCP server...")
def get_graph():
    return _loop().run_until_complete(build_graph())


# ----------------------------------------------------------------------------
# Styles
# ----------------------------------------------------------------------------
CSS = """
<style>
:root {
  --bg: #FAFAFA;
  --surface: #FFFFFF;
  --surface-2: #F8FAFC;
  --border: #E5E7EB;
  --border-strong: #D1D5DB;
  --text: #0F172A;
  --text-muted: #64748B;
  --text-dim: #94A3B8;
  --accent: #0F172A;
  --accent-soft: #F1F5F9;
  --gain: #047857;
  --loss: #B91C1C;
  --gain-bg: #ECFDF5;
  --loss-bg: #FEF2F2;
}

html, body, [class*="css"], table, [data-testid="stMetricValue"] {
  font-variant-numeric: tabular-nums;
  -webkit-font-smoothing: antialiased;
}

.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 100%; }
section[data-testid="stSidebar"] > div { padding-top: 0.5rem; }
section[data-testid="stSidebar"] { background: var(--surface-2); }
[data-testid="stHeader"] { background: transparent; height: 0; }

/* -- Brand header ----------------------------------------------------------*/
.lf-brand { display: flex; align-items: center; gap: 0.85rem; }
.lf-brand-lockup {
  height: 44px;
  width: auto;
  display: block;
}
.lf-status-pill {
  font-size: 0.7rem; color: var(--text-muted);
  border: 1px solid var(--border); border-radius: 999px;
  padding: 0.22rem 0.65rem; background: var(--surface);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  display: inline-block;
  width: fit-content;
  white-space: nowrap;
}
.lf-status-dot {
  display: inline-block;
  width: 6px; height: 6px;
  border-radius: 999px;
  background: var(--gain);
  margin-right: 0.4rem;
  vertical-align: middle;
}

/* -- Sidebar hero + metrics ------------------------------------------------*/
.lf-hero {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.85rem 1rem;
  background: var(--surface);
  margin-bottom: 0.5rem;
}
.lf-hero-label {
  font-size: 0.66rem; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--text-muted); margin-bottom: 0.3rem;
}
.lf-hero-value { font-size: 1.85rem; font-weight: 700; color: var(--text); line-height: 1.05; letter-spacing: -0.02em; }
.lf-hero-delta { font-size: 0.78rem; color: var(--text-muted); margin-top: 0.35rem; }

.lf-metric-mini {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.55rem 0.7rem;
  background: var(--surface);
}
.lf-metric-mini-label {
  font-size: 0.62rem; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--text-muted); margin-bottom: 0.15rem;
}
.lf-metric-mini-value { font-size: 1rem; font-weight: 600; color: var(--text); line-height: 1.1; }
.lf-metric-mini-delta { font-size: 0.7rem; color: var(--text-muted); margin-top: 1px; }

.lf-section {
  font-size: 0.66rem; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--text-muted); font-weight: 600;
  margin: 0.8rem 0 0.45rem 0;
}

/* -- Position cards (denser) ----------------------------------------------*/
.lf-pos {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.15rem 0.5rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.5rem 0.7rem;
  background: var(--surface);
  margin-bottom: 0.35rem;
  font-size: 0.85rem;
  transition: border-color 0.12s, transform 0.12s;
}
.lf-pos:hover { border-color: var(--border-strong); }
.lf-pos-sym { font-weight: 600; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.85rem; }
.lf-pos-meta { font-size: 0.68rem; color: var(--text-muted); }
.lf-pos-val { font-weight: 600; text-align: right; font-size: 0.85rem; }
.lf-pos-pl { font-size: 0.7rem; text-align: right; color: var(--text-muted); }
.gain-pill { background: var(--gain-bg); color: var(--gain); border-radius: 5px; padding: 0 5px; font-size: 0.7rem; font-weight: 600; }
.loss-pill { background: var(--loss-bg); color: var(--loss); border-radius: 5px; padding: 0 5px; font-size: 0.7rem; font-weight: 600; }

/* -- Empty-state agent cards ----------------------------------------------*/
.lf-hero-block {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 0.85rem;
  margin-bottom: 1rem;
}
.lf-intro {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.1rem 1.35rem;
  background: var(--surface);
}
.lf-intro h2 { font-size: 1.3rem; margin: 0 0 0.35rem 0; letter-spacing: -0.01em; font-weight: 600; }
.lf-intro p { color: var(--text-muted); margin: 0; font-size: 0.88rem; line-height: 1.5; }

.lf-flow {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 0.9rem 1.05rem;
  background: var(--surface);
}
.lf-flow-title {
  font-size: 0.7rem; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--text-muted); font-weight: 600; margin-bottom: 0.6rem;
}
.lf-flow-step {
  display: flex; align-items: center; gap: 0.5rem;
  font-size: 0.8rem; color: var(--text);
  padding: 0.2rem 0;
}
.lf-flow-num {
  width: 18px; height: 18px; border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 0.7rem; font-weight: 700;
  display: inline-flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.lf-agent-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}
.lf-agent-card {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.8rem 0.95rem;
  background: var(--surface);
  transition: border-color 0.15s, transform 0.15s;
}
.lf-agent-card:hover { border-color: var(--border-strong); }
.lf-agent-name {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.72rem; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: 0.06em;
  margin-bottom: 0.4rem;
}
.lf-agent-role { font-size: 0.95rem; font-weight: 600; color: var(--text); margin-bottom: 0.3rem; line-height: 1.25; }
.lf-agent-desc { font-size: 0.78rem; color: var(--text-muted); line-height: 1.45; }

/* -- Suggestion chip buttons ----------------------------------------------*/
[data-testid="stHorizontalBlock"] button[kind="secondary"] {
  border: 1px solid var(--border) !important;
  background: var(--surface) !important;
  color: var(--text) !important;
  border-radius: 999px !important;
  padding: 0.45rem 1.05rem !important;
  font-size: 0.86rem !important;
  font-weight: 500 !important;
  transition: border-color 0.15s, background 0.15s, transform 0.15s;
}
[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
  border-color: var(--accent) !important;
  background: var(--accent-soft) !important;
  transform: translateY(-1px);
}

/* -- Chat -----------------------------------------------------------------*/
[data-testid="stChatMessage"] {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.85rem 1.05rem;
  margin-bottom: 0.45rem;
  background: var(--surface);
}

.lf-agent-label {
  display: inline-block;
  font-size: 0.7rem; letter-spacing: 0.06em; text-transform: uppercase;
  color: var(--text-muted); font-weight: 600;
  margin-bottom: 0.5rem;
  padding: 2px 8px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.lf-step {
  display: flex; align-items: center; gap: 0.6rem;
  font-size: 0.82rem; color: var(--text);
  padding: 0.3rem 0;
  border-left: 2px solid var(--border);
  padding-left: 0.75rem;
  margin-left: 0.2rem;
}
.lf-step-kind {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.72rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  min-width: 56px;
}
.lf-step-name { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.8rem; color: var(--text); }

/* -- Trade confirm banner -------------------------------------------------*/
.lf-trade-banner {
  border: 1px solid var(--border-strong);
  border-left: 4px solid var(--accent);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  background: var(--surface);
  margin: 0.75rem 0 0.5rem 0;
}
.lf-trade-banner-title {
  font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--text-muted); font-weight: 600; margin-bottom: 0.35rem;
}
.lf-trade-banner-body { font-size: 0.92rem; color: var(--text); }

button[kind="primary"] {
  background: var(--accent) !important;
  color: #FFFFFF !important;
  border: 1px solid var(--accent) !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
}
button[kind="primary"]:hover { background: #1E293B !important; }

.lf-disclaimer {
  font-size: 0.7rem;
  color: var(--text-dim);
  margin-top: 1rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border);
  text-align: center;
}

.lf-metrics {
  display: flex; gap: 0.85rem; justify-content: flex-end; flex-wrap: wrap;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.72rem; color: var(--text-muted);
  margin-top: 0.5rem;
}
.lf-metric-chip {
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.15rem 0.6rem;
  background: var(--surface);
}
.lf-metric-chip b { color: var(--text); font-weight: 600; margin-right: 0.2rem; }

/* responsive — collapse agent grid on narrow screens */
@media (max-width: 1200px) {
  .lf-agent-grid { grid-template-columns: repeat(2, 1fr); }
  .lf-hero-block { grid-template-columns: 1fr; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
def render_header() -> None:
    lockup_b64 = _asset_b64("llamafolio-horizontal-dark.svg")
    settings = load_settings()
    if settings.llm_provider == "gemini":
        model_label = f"{settings.gemini_model} on Gemini"
    else:
        model_label = f"{settings.groq_model} on Groq"
    col_brand, col_pill, col_actions = st.columns([3, 2, 1], gap="medium", vertical_alignment="center")
    with col_brand:
        st.markdown(
            f"""
            <div class="lf-brand">
              <img class="lf-brand-lockup" src="data:image/svg+xml;base64,{lockup_b64}" alt="Llamafolio"/>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_pill:
        st.markdown(
            f"<div style='text-align:right;'>"
            f"<span class='lf-status-pill'><span class='lf-status-dot'></span>"
            f"Paper &middot; {model_label}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_actions:
        if st.button("New conversation", help="Clear the conversation", use_container_width=True):
            st.session_state["history"] = []
            st.session_state.pop("pending_input", None)
            st.rerun()
    st.markdown(
        "<hr style='margin: 0.5rem 0 1.5rem 0; border: none; border-top: 1px solid var(--border);'/>",
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------------
# Sidebar — dashboard
# ----------------------------------------------------------------------------
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
        f"<div class='lf-pos-pl'><span class='{pl_cls}'>{pl_sign}{p.plpc:.2f}%</span> &middot; {p.weight_pct:.0f}%</div></div>"
        f"</div>"
    )


def _equity_sparkline(history: EquityHistory) -> go.Figure:
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
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#E5E7EB", font=dict(color="#0F172A", size=11)),
    )
    return fig


def _sector_donut(breakdown: dict[str, float]) -> go.Figure:
    fig = go.Figure(
        go.Pie(
            labels=list(breakdown.keys()),
            values=list(breakdown.values()),
            hole=0.65,
            sort=False,
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value:.1f}%<extra></extra>",
            marker=dict(
                colors=["#0F172A", "#334155", "#64748B", "#94A3B8", "#CBD5E1", "#E2E8F0", "#475569"],
                line=dict(color="#FFFFFF", width=2),
            ),
        )
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05,
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


def render_sidebar() -> None:
    settings = load_settings()
    with st.sidebar:
        try:
            acct: AccountSnapshot = load_account(settings)
            positions: list[PositionRow] = load_positions(settings)
            history = load_equity_history(settings, period="1D", timeframe="1Min")
        except Exception as e:  # noqa: BLE001
            st.error(f"Failed to load Alpaca account: {e}")
            return

        # Hero equity with intraday P/L delta if we have history
        delta = None
        if history and history.base_value:
            sign = "+" if history.pnl >= 0 else ""
            cls = "gain" if history.pnl >= 0 else "loss"
            delta = (
                f"<span class='{cls}'>{sign}${history.pnl:,.0f} ({sign}{history.pnl_pct:.2f}%)</span>"
                " <span style='color:var(--text-dim);'>· Today</span>"
            )
        st.markdown(_hero_metric("Total equity", f"${acct.equity:,.0f}", delta), unsafe_allow_html=True)

        # Equity sparkline (intraday, 1-minute resolution)
        if history and len(history.equity) > 1:
            st.plotly_chart(
                _equity_sparkline(history),
                use_container_width=True,
                config={"displayModeBar": False},
            )

        c1, c2 = st.columns(2)
        c1.markdown(
            _mini_metric("Cash", f"${acct.cash:,.0f}", f"{acct.cash_pct:.0f}% of equity"),
            unsafe_allow_html=True,
        )
        c2.markdown(
            _mini_metric("Invested", f"${acct.invested:,.0f}"),
            unsafe_allow_html=True,
        )

        # Positions, denser cards
        st.markdown(
            f"<div class='lf-section'>Positions &middot; {len(positions)}</div>",
            unsafe_allow_html=True,
        )
        if not positions:
            st.markdown(
                "<div class='lf-pos' style='justify-content:center;text-align:center;color:var(--text-muted);'>"
                "No open positions yet.</div>",
                unsafe_allow_html=True,
            )
        else:
            for p in positions:
                st.markdown(_position_card(p), unsafe_allow_html=True)

            st.markdown("<div class='lf-section'>Sector exposure</div>", unsafe_allow_html=True)
            st.plotly_chart(
                _sector_donut(sector_breakdown(positions)),
                use_container_width=True,
                config={"displayModeBar": False},
            )

        st.markdown("<div class='lf-section'>&nbsp;</div>", unsafe_allow_html=True)
        if st.button("Refresh data", use_container_width=True):
            st.rerun()


# ----------------------------------------------------------------------------
# Trade detection
# ----------------------------------------------------------------------------
# A real proposed trade must come from a structured block — either the
# explicit 'Proposed trade' / 'Proposed action' header, or a 'Symbol: X'
# label pattern. Casual mentions of 'trim' or '%' in narrative prose must
# NOT trigger the Confirm/Refuse banner.
_PROPOSED_TRADE_HEADERS = (
    "proposed trade",
    "proposed action",
    "recommended trade",
)
_LABEL_PATTERN = re.compile(
    r"symbol[:\s]+([A-Z]{2,5})\b"
    r".{0,200}?"
    r"\b(buy|sell|trim|reduce)\b"
    r".{0,200}?"
    r"(?:quantity|qty|amount|size)[:\s]+([^\n]+?)(?:\n|$)",
    re.IGNORECASE | re.DOTALL,
)


def detect_proposed_trade(text: str) -> dict | None:
    """Return a concrete trade dict only when the message contains a
    structured proposal block. False positives on casual prose are not
    acceptable — the banner injects a confirmation prompt on click."""
    if not text:
        return None
    low = text.lower()
    if not any(h in low for h in _PROPOSED_TRADE_HEADERS):
        return None
    m = _LABEL_PATTERN.search(text)
    if not m:
        return None
    symbol, side, qty_raw = m.group(1), m.group(2).lower(), m.group(3).strip()
    if side in ("trim", "reduce"):
        side = "sell"
    # Clean up quantity formatting
    qty = qty_raw.split("(")[0].strip().rstrip(".,")
    if not qty:
        return None
    return {"symbol": symbol.upper(), "side": side, "qty": qty}


# ----------------------------------------------------------------------------
# Empty state — intro, agent cards, how it works
# ----------------------------------------------------------------------------
AGENTS = [
    {
        "name": "portfolio_analyst",
        "role": "Reads your portfolio",
        "desc": "Computes composition, sector exposure on invested capital, and flags concentration above 40%.",
    },
    {
        "name": "research_agent",
        "role": "Gathers context",
        "desc": "Pulls news, snapshots, fundamentals and web sources to back any claim with citations.",
    },
    {
        "name": "risk_manager",
        "role": "Vets every proposal",
        "desc": "Checks position sizing, sector exposure post-trade and volatility before any trade idea reaches you.",
    },
    {
        "name": "executor",
        "role": "Places paper orders",
        "desc": "Only invoked after you explicitly confirm. Refuses ambiguous instructions on purpose.",
    },
]


def render_welcome() -> None:
    st.markdown(
        """
        <div class="lf-hero-block">
          <div class="lf-intro">
            <h2>Ask anything about your portfolio</h2>
            <p>Llamafolio routes your question across four specialist agents, then synthesises a single answer with sources. Trades are <strong>never</strong> executed without your explicit confirmation &mdash; you get a confirm/refuse button when an order is proposed.</p>
          </div>
          <div class="lf-flow">
            <div class="lf-flow-title">How a turn flows</div>
            <div class="lf-flow-step"><span class="lf-flow-num">1</span> Supervisor reads the question</div>
            <div class="lf-flow-step"><span class="lf-flow-num">2</span> Routes to the right specialist(s)</div>
            <div class="lf-flow-step"><span class="lf-flow-num">3</span> Specialists call MCP &amp; web tools</div>
            <div class="lf-flow-step"><span class="lf-flow-num">4</span> Supervisor synthesises and ends</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cards_html = "".join(
        f"<div class='lf-agent-card'>"
        f"<div class='lf-agent-name'>{a['name']}</div>"
        f"<div class='lf-agent-role'>{a['role']}</div>"
        f"<div class='lf-agent-desc'>{a['desc']}</div>"
        f"</div>"
        for a in AGENTS
    )
    st.markdown(f"<div class='lf-agent-grid'>{cards_html}</div>", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Suggestions
# ----------------------------------------------------------------------------
SUGGESTIONS = [
    ("Analyse my sector exposure", "Analyse my sector exposure and flag any concentration risk."),
    ("Recent news on my holdings", "Summarise recent news on each of my current holdings."),
    ("Suggest a rebalancing", "Suggest ONE position to trim with research and a risk check. Do not execute."),
    ("Account snapshot", "Give me a one-paragraph snapshot of my account state."),
]


def render_suggestions(key_prefix: str = "sug") -> None:
    def _set_pending(q: str) -> None:
        st.session_state["pending_input"] = q

    cols = st.columns(len(SUGGESTIONS))
    for col, (label, query) in zip(cols, SUGGESTIONS):
        col.button(
            label,
            use_container_width=True,
            key=f"{key_prefix}_{label}",
            on_click=_set_pending,
            args=(query,),
        )


# ----------------------------------------------------------------------------
# Agent step labels (timeline)
# ----------------------------------------------------------------------------
def _step_label(msg) -> tuple[str, str] | None:
    name = getattr(msg, "name", None) or "supervisor"
    if isinstance(msg, AIMessage) and msg.tool_calls:
        for tc in msg.tool_calls:
            t = tc["name"]
            if t.startswith("transfer_to_"):
                target = t.removeprefix("transfer_to_")
                return ("route", f"<span class='lf-step-name'>{target}</span>")
            if t.startswith("transfer_back"):
                return ("done", f"<span class='lf-step-name'>{name}</span>")
            return ("tool", f"<span class='lf-step-name'>{name} &middot; {t}</span>")
    return None


HANDOFF_NOISE = ("transferred back", "transferring back", "handing back")


def _content_text(m) -> str:
    """Extract text content from a LangChain message, handling both the
    classic str shape and the newer list-of-parts shape that Gemini 3.x
    uses (e.g. [{'type': 'text', 'text': '...'}])."""
    c = getattr(m, "content", "") or ""
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts: list[str] = []
        for chunk in c:
            if isinstance(chunk, str):
                parts.append(chunk)
            elif isinstance(chunk, dict):
                text = chunk.get("text") or chunk.get("content") or ""
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)
    return str(c)


# ----------------------------------------------------------------------------
# Trade actions
# ----------------------------------------------------------------------------
def render_trade_actions(agent_msgs: list) -> None:
    # If the executor already placed an order in this turn, the loop is
    # closed — never surface a fresh Confirm/Refuse banner, even if some
    # earlier message in the trace still contains a proposal block. This
    # prevents the user from accidentally placing a duplicate order by
    # clicking the banner that re-appears after the success message.
    for m in agent_msgs:
        if getattr(m, "name", None) == "executor":
            text_low = _content_text(m).lower()
            if "order placed" in text_low or "accepted" in text_low:
                return

    trade = None
    for m in agent_msgs:
        # Also skip executor messages while scanning for proposals — their
        # success block echoes the symbol/side/quantity and would match
        # the detector.
        if getattr(m, "name", None) == "executor":
            continue
        trade = detect_proposed_trade(_content_text(m))
        if trade:
            break
    if not trade:
        return
    st.markdown(
        f"<div class='lf-trade-banner'>"
        f"<div class='lf-trade-banner-title'>Action requested</div>"
        f"<div class='lf-trade-banner-body'>"
        f"<b>{trade['side'].upper()} {trade['symbol']}</b> &middot; {trade['qty']}"
        f"</div></div>",
        unsafe_allow_html=True,
    )
    # Use on_click callbacks rather than the if-block + st.rerun() pattern.
    # When the banner is rendered at the very end of a streaming turn, an
    # explicit st.rerun() inside the if-block sometimes leaves Streamlit in
    # a state where the click is registered but the rerun never starts —
    # the user clicks Confirm and nothing visible happens. Callbacks fire
    # before the natural rerun and are robust to that timing.
    def _confirm():
        st.session_state["pending_input"] = (
            f"confirm {trade['side']} {trade['symbol']} {trade['qty']}"
        )

    def _refuse():
        st.session_state["pending_input"] = (
            f"do not execute the proposed {trade['side']} of {trade['symbol']}. close the loop."
        )

    c1, c2, _ = st.columns([1, 1, 4])
    c1.button(
        "Confirm",
        type="primary",
        key=f"confirm_{trade['symbol']}",
        use_container_width=True,
        on_click=_confirm,
    )
    c2.button(
        "Refuse",
        key=f"refuse_{trade['symbol']}",
        use_container_width=True,
        on_click=_refuse,
    )


# ----------------------------------------------------------------------------
# Chat
# ----------------------------------------------------------------------------
def render_chat() -> None:
    if "history" not in st.session_state:
        st.session_state.history = []

    show_welcome = not any(isinstance(m, HumanMessage) for m in st.session_state.history)
    if show_welcome:
        render_welcome()
        render_suggestions("welcome")

    for msg in st.session_state.history:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user", avatar=USER_AVATAR):
                st.markdown(_content_text(msg))
        elif isinstance(msg, AIMessage) and _content_text(msg) and not msg.tool_calls:
            with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
                name = getattr(msg, "name", None) or "supervisor"
                st.markdown(
                    f"<span class='lf-agent-label'>{name.replace('_', ' ')}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(_content_text(msg))

    typed = st.chat_input("Ask anything about your portfolio.")
    pending = st.session_state.pop("pending_input", None)
    prompt = pending or typed

    if not show_welcome:
        st.markdown("<div class='lf-section'>Quick prompts</div>", unsafe_allow_html=True)
        render_suggestions("persist")

    if not prompt:
        return

    # Store the original prompt in history for display, but send a wrapped
    # version (with auto-fetched portfolio context) to the graph. This is
    # the core cost optimisation: one Alpaca read on the host fills the
    # LLM's context with everything the analyst would otherwise fetch via
    # 10+ MCP tool round-trips.
    user_msg = HumanMessage(content=prompt)
    st.session_state.history.append(user_msg)
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    settings = load_settings()
    try:
        ctx = render_portfolio_context(
            load_account(settings),
            load_positions(settings),
            load_equity_history(settings, period="1D", timeframe="1Min"),
        )
        wrapped_prompt = f"{ctx}\n\nUser question: {prompt}"
    except Exception:  # noqa: BLE001
        # If pre-fetch fails, fall back to the raw prompt; specialists can
        # still call their tools.
        wrapped_prompt = prompt
    message_list = [*st.session_state.history[:-1], HumanMessage(content=wrapped_prompt)]

    # Streaming: render each agent message in its own bubble as soon as it
    # arrives from LangGraph (stream_mode='updates'), and surface routing /
    # tool-call steps in the timeline live. We drive the async generator
    # synchronously by awaiting each chunk on the persistent session loop,
    # so the cached graph and its MCP connections stay alive across yields.
    loop = _loop()
    graph = get_graph()
    status = st.status("Thinking...", expanded=True)
    agent_msgs: list = []
    seen_ids: set[str] = set()

    # Per-turn metrics: counts visible-tool calls (excluding handoffs),
    # LLM round-trips (= each AIMessage emitted by a model), agents touched,
    # and total wall-clock time. Surfaced as a small footer chip row so the
    # cost-optimisation gains are visible to the user, not just in logs.
    metrics = {"agents": set(), "tool_calls": 0, "llm_calls": 0}
    t_start = time.perf_counter()

    async def _anext(it):
        return await it.__anext__()

    agen = graph.astream(
        {"messages": message_list},
        stream_mode="updates",
    )

    try:
        while True:
            try:
                chunk = loop.run_until_complete(_anext(agen))
            except StopAsyncIteration:
                break

            for node_name, node_state in chunk.items():
                if not isinstance(node_state, dict):
                    continue
                for m in node_state.get("messages", []):
                    msg_id = getattr(m, "id", None) or str(id(m))
                    if msg_id in seen_ids:
                        continue
                    seen_ids.add(msg_id)

                    # Metrics: every AIMessage = one LLM round-trip. Every
                    # non-handoff tool_call inside it counts as a real tool
                    # call. Track the set of agents touched too.
                    if isinstance(m, AIMessage):
                        metrics["llm_calls"] += 1
                        name = getattr(m, "name", None)
                        if name:
                            metrics["agents"].add(name)
                        for tc in (m.tool_calls or []):
                            t = tc["name"]
                            if not (t.startswith("transfer_to_") or t.startswith("transfer_back")):
                                metrics["tool_calls"] += 1

                    step = _step_label(m)
                    if step:
                        kind, body = step
                        status.markdown(
                            f"<div class='lf-step'>"
                            f"<span class='lf-step-kind'>{kind}</span>{body}"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                    text = _content_text(m)
                    if (
                        isinstance(m, AIMessage)
                        and text
                        and not m.tool_calls
                        and not any(s in text.lower() for s in HANDOFF_NOISE)
                    ):
                        with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
                            name = getattr(m, "name", None) or "supervisor"
                            st.markdown(
                                f"<span class='lf-agent-label'>{name.replace('_', ' ')}</span>",
                                unsafe_allow_html=True,
                            )
                            st.markdown(text)
                        st.session_state.history.append(m)
                        agent_msgs.append(m)
    except Exception as e:  # noqa: BLE001
        status.update(label="Agent error", state="error", expanded=True)
        err = str(e)
        if "tool_use_failed" in err or "was not in request.tools" in err:
            hint = (
                "The LLM emitted an invalid tool call. Try rephrasing the "
                "question, or retry — this is a known limitation."
            )
        elif "rate_limit" in err.lower() or "resource_exhausted" in err.lower():
            hint = "Provider rate limit reached. Try again in a minute, or switch model in .env."
        else:
            hint = "Try again, or check the logs."
        st.error(f"**Agent failed.** {hint}\n\n```\n{err[:600]}\n```")
        if st.session_state.history and isinstance(st.session_state.history[-1], HumanMessage):
            st.session_state.history.pop()
        return
    finally:
        status.update(label="Done", state="complete", expanded=False)

    render_trade_actions(agent_msgs)

    # Per-turn metrics footer so the cost-optimisation gains are visible.
    elapsed = time.perf_counter() - t_start
    n_agents = len(metrics["agents"] - {"supervisor"})
    st.markdown(
        f"<div class='lf-metrics'>"
        f"<span class='lf-metric-chip'><b>{n_agents}</b>specialists</span>"
        f"<span class='lf-metric-chip'><b>{metrics['tool_calls']}</b>tool calls</span>"
        f"<span class='lf-metric-chip'><b>{metrics['llm_calls']}</b>LLM round-trips</span>"
        f"<span class='lf-metric-chip'><b>{elapsed:.1f}s</b>total</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class='lf-disclaimer'>Paper trading account &middot; informational only &middot; not investment advice.</div>",
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------------
# Entry
# ----------------------------------------------------------------------------
render_sidebar()
render_header()
render_chat()
