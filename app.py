"""Llamafolio — Streamlit UI.

Design direction: Bloomberg-meets-Linear. Data-forward, sober, light theme.
Custom CSS handles typography, spacing, and the agent step timeline.
"""
from __future__ import annotations

import asyncio

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from llamafolio.config import load_settings
from llamafolio.graph import build_graph
from llamafolio.ui.portfolio_data import (
    AccountSnapshot,
    PositionRow,
    load_account,
    load_positions,
    sector_breakdown,
)

st.set_page_config(
    page_title="Llamafolio",
    page_icon="🦙",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ----------------------------------------------------------------------------
# Async glue
# ----------------------------------------------------------------------------
def _loop() -> asyncio.AbstractEventLoop:
    if "_loop" not in st.session_state:
        st.session_state["_loop"] = asyncio.new_event_loop()
    return st.session_state["_loop"]


@st.cache_resource(show_spinner="Booting Llamafolio (multi-agent graph + Alpaca MCP)...")
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

/* Global tabular nums */
html, body, [class*="css"], table, [data-testid="stMetricValue"] {
  font-variant-numeric: tabular-nums;
  -webkit-font-smoothing: antialiased;
}

/* Tighten default Streamlit padding */
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 100%; }
section[data-testid="stSidebar"] > div { padding-top: 1rem; }

/* Hide default Streamlit header chrome */
[data-testid="stHeader"] { background: transparent; height: 0; }

/* Brand header */
.lf-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 0 1rem 0;
  border-bottom: 1px solid var(--border);
  margin-bottom: 1.5rem;
}
.lf-brand { display: flex; align-items: center; gap: 0.75rem; }
.lf-brand-mark {
  width: 36px; height: 36px;
  background: var(--accent);
  color: #FFFFFF;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.1rem;
}
.lf-brand-title { font-size: 1.25rem; font-weight: 600; color: var(--text); letter-spacing: -0.01em; }
.lf-brand-sub { font-size: 0.8rem; color: var(--text-muted); margin-top: 1px; }
.lf-status-pill {
  display: inline-flex; align-items: center; gap: 0.4rem;
  font-size: 0.75rem; color: var(--text-muted);
  border: 1px solid var(--border); border-radius: 999px;
  padding: 0.25rem 0.65rem; background: var(--surface);
}
.lf-status-dot { width: 6px; height: 6px; border-radius: 999px; background: var(--gain); display: inline-block; }

/* Sidebar metric cards */
.lf-metric {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.75rem 0.9rem;
  background: var(--surface);
  margin-bottom: 0.5rem;
}
.lf-metric-label {
  font-size: 0.7rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
}
.lf-metric-value { font-size: 1.4rem; font-weight: 600; color: var(--text); line-height: 1.1; }
.lf-metric-delta { font-size: 0.8rem; color: var(--text-muted); margin-top: 2px; }

/* Section header in sidebar */
.lf-section {
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: 600;
  margin: 1rem 0 0.5rem 0;
}

/* Position row */
.lf-pos {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.25rem 0.5rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.5rem 0.7rem;
  background: var(--surface);
  margin-bottom: 0.35rem;
}
.lf-pos-sym { font-weight: 600; letter-spacing: 0.02em; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.lf-pos-meta { font-size: 0.72rem; color: var(--text-muted); }
.lf-pos-val { font-weight: 600; text-align: right; }
.lf-pos-pl { font-size: 0.78rem; text-align: right; }
.gain { color: var(--gain); }
.loss { color: var(--loss); }
.gain-pill { background: var(--gain-bg); color: var(--gain); border-radius: 6px; padding: 1px 6px; font-size: 0.72rem; font-weight: 600; }
.loss-pill { background: var(--loss-bg); color: var(--loss); border-radius: 6px; padding: 1px 6px; font-size: 0.72rem; font-weight: 600; }

/* Welcome card */
.lf-welcome {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.5rem;
  background: var(--surface);
  margin-bottom: 1rem;
}
.lf-welcome h2 { font-size: 1.4rem; margin: 0 0 0.35rem 0; letter-spacing: -0.01em; font-weight: 600; }
.lf-welcome p { color: var(--text-muted); margin: 0; font-size: 0.92rem; line-height: 1.5; }

/* Suggestion chip buttons (target Streamlit buttons) */
[data-testid="stHorizontalBlock"] button[kind="secondary"] {
  border: 1px solid var(--border) !important;
  background: var(--surface) !important;
  color: var(--text) !important;
  border-radius: 999px !important;
  padding: 0.4rem 0.9rem !important;
  font-size: 0.85rem !important;
  font-weight: 500 !important;
  transition: border-color 0.15s, background 0.15s;
}
[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
  border-color: var(--accent) !important;
  background: var(--accent-soft) !important;
}

/* Chat message styling */
[data-testid="stChatMessage"] {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.9rem 1.1rem;
  margin-bottom: 0.5rem;
  background: var(--surface);
}

/* Agent step timeline */
.lf-step {
  display: flex; align-items: center; gap: 0.6rem;
  font-size: 0.85rem; color: var(--text);
  padding: 0.35rem 0;
  border-left: 2px solid var(--border);
  padding-left: 0.75rem;
  margin-left: 0.25rem;
}
.lf-step-icon {
  width: 18px; height: 18px; border-radius: 999px;
  background: var(--accent-soft); color: var(--accent);
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 0.7rem; font-weight: 700;
}
.lf-step-name { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.8rem; color: var(--text-muted); }

/* Disclaimer footer */
.lf-disclaimer { font-size: 0.72rem; color: var(--text-dim); margin-top: 0.5rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
def render_header() -> None:
    st.markdown(
        """
        <div class="lf-header">
          <div class="lf-brand">
            <div class="lf-brand-mark">🦙</div>
            <div>
              <div class="lf-brand-title">Llamafolio</div>
              <div class="lf-brand-sub">AI portfolio advisor · Alpaca paper trading</div>
            </div>
          </div>
          <div class="lf-status-pill">
            <span class="lf-status-dot"></span> PAPER · Llama 3.3 70B via Groq
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
def _metric(label: str, value: str, delta: str | None = None) -> str:
    delta_html = f"<div class='lf-metric-delta'>{delta}</div>" if delta else ""
    return (
        f"<div class='lf-metric'>"
        f"<div class='lf-metric-label'>{label}</div>"
        f"<div class='lf-metric-value'>{value}</div>"
        f"{delta_html}</div>"
    )


def _position_card(p: PositionRow) -> str:
    pl_cls = "gain-pill" if p.plpc >= 0 else "loss-pill"
    pl_sign = "+" if p.plpc >= 0 else ""
    return (
        f"<div class='lf-pos'>"
        f"<div><div class='lf-pos-sym'>{p.symbol}</div>"
        f"<div class='lf-pos-meta'>{p.sector} · {p.qty:g} sh</div></div>"
        f"<div><div class='lf-pos-val'>${p.market_value:,.0f}</div>"
        f"<div class='lf-pos-pl'><span class='{pl_cls}'>{pl_sign}{p.plpc:.2f}%</span> · {p.weight_pct:.0f}%</div></div>"
        f"</div>"
    )


def _sector_donut(breakdown: dict[str, float]) -> go.Figure:
    fig = go.Figure(
        go.Pie(
            labels=list(breakdown.keys()),
            values=list(breakdown.values()),
            hole=0.62,
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
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05, font=dict(size=11)),
        margin=dict(l=0, r=0, t=10, b=0),
        height=220,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="ui-sans-serif, system-ui, sans-serif", color="#0F172A"),
    )
    return fig


def render_sidebar() -> None:
    settings = load_settings()
    with st.sidebar:
        st.markdown("<div class='lf-section'>Account</div>", unsafe_allow_html=True)
        try:
            acct: AccountSnapshot = load_account(settings)
            positions: list[PositionRow] = load_positions(settings)
        except Exception as e:  # noqa: BLE001
            st.error(f"Failed to load Alpaca account: {e}")
            return

        st.markdown(_metric("Equity", f"${acct.equity:,.0f}"), unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.markdown(_metric("Cash", f"${acct.cash:,.0f}", f"{acct.cash_pct:.0f}%"), unsafe_allow_html=True)
        c2.markdown(_metric("Invested", f"${acct.invested:,.0f}"), unsafe_allow_html=True)

        st.markdown("<div class='lf-section'>Positions</div>", unsafe_allow_html=True)
        if not positions:
            st.markdown(
                "<div class='lf-pos' style='justify-content:center;text-align:center;color:var(--text-muted);'>"
                "No open positions yet.<br><span style='font-size:0.72rem;'>Orders may be queued until market open (15:30 CET).</span>"
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            for p in positions:
                st.markdown(_position_card(p), unsafe_allow_html=True)

            st.markdown("<div class='lf-section'>Sector exposure</div>", unsafe_allow_html=True)
            st.plotly_chart(_sector_donut(sector_breakdown(positions)), use_container_width=True, config={"displayModeBar": False})

        st.markdown("<div class='lf-section'>&nbsp;</div>", unsafe_allow_html=True)
        if st.button("Refresh", use_container_width=True):
            st.rerun()


# ----------------------------------------------------------------------------
# Main — welcome + chat
# ----------------------------------------------------------------------------
SUGGESTIONS = [
    "📊 Analyse my sector exposure",
    "🔍 What's happening with NVDA?",
    "⚖ Suggest a rebalancing",
    "📰 Recent news on my holdings",
]


def render_welcome() -> None:
    st.markdown(
        """
        <div class="lf-welcome">
          <h2>Portfolio advisor</h2>
          <p>Llamafolio routes your question across four specialist agents — analyst, research, risk, executor — and synthesises a single answer with sources. Trades are <b>never</b> executed without your explicit confirmation.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(len(SUGGESTIONS))
    for col, s in zip(cols, SUGGESTIONS):
        if col.button(s, use_container_width=True, key=f"sug_{s}"):
            st.session_state["pending_input"] = s.split(" ", 1)[1]
            st.rerun()


def _step_label(msg) -> tuple[str, str] | None:
    """Return (icon, label) for a step row, or None to skip."""
    name = getattr(msg, "name", None)
    if isinstance(msg, AIMessage) and msg.tool_calls:
        for tc in msg.tool_calls:
            t = tc["name"]
            if t.startswith("transfer_to_"):
                target = t.removeprefix("transfer_to_")
                return ("→", f"routing to <span class='lf-step-name'>{target}</span>")
            if t.startswith("transfer_back"):
                return ("←", f"<span class='lf-step-name'>{name or '?'}</span> handing back")
            return ("⚙", f"<span class='lf-step-name'>{name or 'agent'}</span> · {t}")
    return None


def render_chat() -> None:
    if "history" not in st.session_state:
        st.session_state.history = []

    show_welcome = not any(isinstance(m, HumanMessage) for m in st.session_state.history)
    if show_welcome:
        render_welcome()

    for msg in st.session_state.history:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user"):
                st.markdown(msg.content)
        elif isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            with st.chat_message("assistant"):
                st.markdown(msg.content)

    # Always render the input so it never disappears after a chip click.
    typed = st.chat_input("Ask anything about your portfolio.")
    pending = st.session_state.pop("pending_input", None)
    prompt = pending or typed
    if not prompt:
        return

    user_msg = HumanMessage(content=prompt)
    st.session_state.history.append(user_msg)
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        status = st.status("Thinking...", expanded=True)
        graph = get_graph()
        result = _loop().run_until_complete(
            graph.ainvoke({"messages": st.session_state.history})
        )
        new_msgs = result["messages"][len(st.session_state.history) - 1 :]

        # 1) Live timeline of routing + tool calls
        for m in new_msgs:
            step = _step_label(m)
            if step:
                icon, label = step
                status.markdown(
                    f"<div class='lf-step'><span class='lf-step-icon'>{icon}</span>{label}</div>",
                    unsafe_allow_html=True,
                )
        status.update(label="Done", state="complete", expanded=False)

        # 2) Render every agent content message produced during this turn.
        #    Skip pure handoff acks (very short messages from the supervisor
        #    that just say "transferred back" etc.).
        HANDOFF_NOISE = ("transferred back", "transferring back", "handing back")
        agent_msgs = [
            m for m in new_msgs
            if isinstance(m, AIMessage) and m.content and not m.tool_calls
            and not any(s in m.content.lower() for s in HANDOFF_NOISE)
        ]

        for m in agent_msgs:
            name = getattr(m, "name", None) or "supervisor"
            if name != "supervisor":
                st.markdown(
                    f"<div class='lf-section' style='margin-top:0.75rem;'>{name.replace('_', ' ')}</div>",
                    unsafe_allow_html=True,
                )
            st.markdown(m.content)
            st.session_state.history.append(m)

        st.markdown(
            "<div class='lf-disclaimer'>Paper trading account · informational only · not investment advice.</div>",
            unsafe_allow_html=True,
        )


# ----------------------------------------------------------------------------
# Entry
# ----------------------------------------------------------------------------
render_sidebar()
render_header()
render_chat()
