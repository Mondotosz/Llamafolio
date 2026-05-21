"""Llamafolio — Streamlit UI.

Light, data-forward theme. No emojis. Custom CSS handles typography,
spacing, the agent step timeline, and trade-confirmation buttons.
"""
from __future__ import annotations

import asyncio
import re

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
    page_icon=None,
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
section[data-testid="stSidebar"] > div { padding-top: 1rem; }
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
  width: 32px; height: 32px;
  background: var(--accent);
  color: #FFFFFF;
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.9rem; font-weight: 700;
  letter-spacing: -0.02em;
}
.lf-brand-title { font-size: 1.2rem; font-weight: 600; color: var(--text); letter-spacing: -0.01em; }
.lf-brand-sub { font-size: 0.78rem; color: var(--text-muted); margin-top: 1px; }
.lf-header-actions { display: flex; align-items: center; gap: 0.5rem; }
.lf-status-pill {
  font-size: 0.72rem; color: var(--text-muted);
  border: 1px solid var(--border); border-radius: 999px;
  padding: 0.25rem 0.7rem; background: var(--surface);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

/* Sidebar metric cards */
.lf-metric {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.7rem 0.85rem;
  background: var(--surface);
  margin-bottom: 0.5rem;
}
.lf-metric-label {
  font-size: 0.68rem; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--text-muted); margin-bottom: 0.25rem;
}
.lf-metric-value { font-size: 1.35rem; font-weight: 600; color: var(--text); line-height: 1.1; }
.lf-metric-delta { font-size: 0.78rem; color: var(--text-muted); margin-top: 2px; }

.lf-section {
  font-size: 0.7rem; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--text-muted); font-weight: 600;
  margin: 1rem 0 0.5rem 0;
}

/* Position cards */
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
.lf-pos-sym { font-weight: 600; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.lf-pos-meta { font-size: 0.72rem; color: var(--text-muted); }
.lf-pos-val { font-weight: 600; text-align: right; }
.lf-pos-pl { font-size: 0.78rem; text-align: right; }
.gain-pill { background: var(--gain-bg); color: var(--gain); border-radius: 6px; padding: 1px 6px; font-size: 0.72rem; font-weight: 600; }
.loss-pill { background: var(--loss-bg); color: var(--loss); border-radius: 6px; padding: 1px 6px; font-size: 0.72rem; font-weight: 600; }

/* Welcome card */
.lf-welcome {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  background: var(--surface);
  margin-bottom: 1rem;
}
.lf-welcome h2 { font-size: 1.25rem; margin: 0 0 0.4rem 0; letter-spacing: -0.01em; font-weight: 600; }
.lf-welcome p { color: var(--text-muted); margin: 0; font-size: 0.9rem; line-height: 1.5; }

/* Secondary buttons styled as chips */
[data-testid="stHorizontalBlock"] button[kind="secondary"] {
  border: 1px solid var(--border) !important;
  background: var(--surface) !important;
  color: var(--text) !important;
  border-radius: 999px !important;
  padding: 0.35rem 0.9rem !important;
  font-size: 0.82rem !important;
  font-weight: 500 !important;
  transition: border-color 0.15s, background 0.15s;
}
[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
  border-color: var(--accent) !important;
  background: var(--accent-soft) !important;
}

/* Chat message wrapper */
[data-testid="stChatMessage"] {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.85rem 1.05rem;
  margin-bottom: 0.45rem;
  background: var(--surface);
}

/* Per-agent label inside an assistant message */
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

/* Step timeline (inside the thinking expander) */
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

/* Confirm / Refuse trade banner */
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

/* Primary action button = dark accent */
button[kind="primary"] {
  background: var(--accent) !important;
  color: #FFFFFF !important;
  border: 1px solid var(--accent) !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
}
button[kind="primary"]:hover { background: #1E293B !important; }

.lf-disclaimer { font-size: 0.72rem; color: var(--text-dim); margin-top: 0.5rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
def render_header() -> None:
    col_brand, col_actions = st.columns([5, 1])
    with col_brand:
        st.markdown(
            """
            <div class="lf-brand">
              <div class="lf-brand-mark">L</div>
              <div>
                <div class="lf-brand-title">Llamafolio</div>
                <div class="lf-brand-sub">AI portfolio advisor &middot; Alpaca paper trading</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_actions:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown(
                "<div class='lf-status-pill' style='margin-top:0.5rem;'>Paper</div>",
                unsafe_allow_html=True,
            )
        with c2:
            if st.button("New", help="Clear the conversation", use_container_width=True):
                st.session_state["history"] = []
                st.session_state.pop("pending_input", None)
                st.rerun()
    st.markdown("<hr style='margin: 0.75rem 0 1.25rem 0; border: none; border-top: 1px solid var(--border);'/>", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Sidebar — dashboard
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
        f"<div class='lf-pos-meta'>{p.sector} &middot; {p.qty:g} sh</div></div>"
        f"<div><div class='lf-pos-val'>${p.market_value:,.0f}</div>"
        f"<div class='lf-pos-pl'><span class='{pl_cls}'>{pl_sign}{p.plpc:.2f}%</span> &middot; {p.weight_pct:.0f}%</div></div>"
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
                "No open positions yet.</div>",
                unsafe_allow_html=True,
            )
        else:
            for p in positions:
                st.markdown(_position_card(p), unsafe_allow_html=True)

            st.markdown("<div class='lf-section'>Sector exposure</div>", unsafe_allow_html=True)
            st.plotly_chart(_sector_donut(sector_breakdown(positions)), use_container_width=True, config={"displayModeBar": False})

        st.markdown("<div class='lf-section'>&nbsp;</div>", unsafe_allow_html=True)
        if st.button("Refresh data", use_container_width=True):
            st.rerun()


# ----------------------------------------------------------------------------
# Trade detection — parse a proposed trade out of an assistant message
# ----------------------------------------------------------------------------
TRADE_TRIGGERS = ("proposed trade", "proposal", "recommendation", "trim", "rebalance")

def detect_proposed_trade(text: str) -> dict | None:
    """Return a dict with symbol/side/qty when the assistant has proposed a
    concrete trade, else None. Heuristic — robust enough for the POC."""
    if not text:
        return None
    low = text.lower()
    if not any(t in low for t in TRADE_TRIGGERS):
        return None

    sym_m = re.search(r"\b([A-Z]{1,5})\b\s*(?:\(|,|\.|$|\s)", text)
    side_m = re.search(r"\b(buy|sell|trim|reduce)\b", text, re.IGNORECASE)
    # Look for a percentage or share quantity
    qty_pct = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    qty_sh = re.search(r"(\d+(?:\.\d+)?)\s*share", text, re.IGNORECASE)
    qty_usd = re.search(r"\$\s?(\d[\d,]*)", text)

    if not (sym_m and side_m):
        return None
    side = side_m.group(1).lower()
    if side in ("trim", "reduce"):
        side = "sell"
    qty = None
    if qty_pct:
        qty = f"{qty_pct.group(1)}%"
    elif qty_sh:
        qty = f"{qty_sh.group(1)} shares"
    elif qty_usd:
        qty = f"${qty_usd.group(1)}"
    if not qty:
        return None
    return {"symbol": sym_m.group(1), "side": side, "qty": qty}


# ----------------------------------------------------------------------------
# Main — welcome, chat, suggestions
# ----------------------------------------------------------------------------
SUGGESTIONS = [
    ("Analyse my sector exposure", "Analyse my sector exposure and flag any concentration risk."),
    ("Recent news on my holdings", "Summarise recent news on each of my current holdings."),
    ("Suggest a rebalancing", "Suggest ONE position to trim with research and a risk check. Do not execute."),
    ("Account snapshot", "Give me a one-paragraph snapshot of my account state."),
]


def render_welcome() -> None:
    st.markdown(
        """
        <div class="lf-welcome">
          <h2>Portfolio advisor</h2>
          <p>Ask about your portfolio and Llamafolio routes the question across four specialist agents (analyst, research, risk, executor), then synthesises a single answer with sources. Trades are never executed without your explicit confirmation.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_suggestions(key_prefix: str = "sug") -> None:
    cols = st.columns(len(SUGGESTIONS))
    for col, (label, query) in zip(cols, SUGGESTIONS):
        if col.button(label, use_container_width=True, key=f"{key_prefix}_{label}"):
            st.session_state["pending_input"] = query
            st.rerun()


def _step_label(msg) -> tuple[str, str, str] | None:
    """Return (kind, body_html, name) or None for non-step messages."""
    name = getattr(msg, "name", None) or "supervisor"
    if isinstance(msg, AIMessage) and msg.tool_calls:
        for tc in msg.tool_calls:
            t = tc["name"]
            if t.startswith("transfer_to_"):
                target = t.removeprefix("transfer_to_")
                return ("route", f"<span class='lf-step-name'>{target}</span>", name)
            if t.startswith("transfer_back"):
                return ("done", f"<span class='lf-step-name'>{name}</span>", name)
            return ("tool", f"<span class='lf-step-name'>{name} &middot; {t}</span>", name)
    return None


HANDOFF_NOISE = ("transferred back", "transferring back", "handing back")


def render_agent_messages(new_msgs: list, container) -> None:
    """Render every substantive agent message produced this turn."""
    agent_msgs = [
        m for m in new_msgs
        if isinstance(m, AIMessage) and m.content and not m.tool_calls
        and not any(s in m.content.lower() for s in HANDOFF_NOISE)
    ]
    for m in agent_msgs:
        name = getattr(m, "name", None) or "supervisor"
        with container:
            st.markdown(
                f"<span class='lf-agent-label'>{name.replace('_', ' ')}</span>",
                unsafe_allow_html=True,
            )
            st.markdown(m.content)
        st.session_state.history.append(m)
    return agent_msgs


def render_trade_actions(agent_msgs: list) -> None:
    """If any agent message proposed a concrete trade, show Confirm / Refuse."""
    trade = None
    for m in agent_msgs:
        trade = detect_proposed_trade(m.content)
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
    c1, c2, _ = st.columns([1, 1, 4])
    with c1:
        if st.button("Confirm", type="primary", key=f"confirm_{trade['symbol']}", use_container_width=True):
            st.session_state["pending_input"] = (
                f"confirm {trade['side']} {trade['symbol']} {trade['qty']}"
            )
            st.rerun()
    with c2:
        if st.button("Refuse", key=f"refuse_{trade['symbol']}", use_container_width=True):
            st.session_state["pending_input"] = (
                f"do not execute the proposed {trade['side']} of {trade['symbol']}. close the loop."
            )
            st.rerun()


def render_chat() -> None:
    if "history" not in st.session_state:
        st.session_state.history = []

    show_welcome = not any(isinstance(m, HumanMessage) for m in st.session_state.history)
    if show_welcome:
        render_welcome()
        render_suggestions("welcome")

    for msg in st.session_state.history:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user"):
                st.markdown(msg.content)
        elif isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            with st.chat_message("assistant"):
                name = getattr(msg, "name", None) or "supervisor"
                st.markdown(
                    f"<span class='lf-agent-label'>{name.replace('_', ' ')}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(msg.content)

    # Always render the input so it never disappears after a chip click.
    typed = st.chat_input("Ask anything about your portfolio.")
    pending = st.session_state.pop("pending_input", None)
    prompt = pending or typed

    # Persistent suggestions stay visible above the input after the welcome
    # disappears, so the user always has quick starters available.
    if not show_welcome:
        st.markdown("<div class='lf-section'>Quick prompts</div>", unsafe_allow_html=True)
        render_suggestions("persist")

    if not prompt:
        return

    user_msg = HumanMessage(content=prompt)
    st.session_state.history.append(user_msg)
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        status = st.status("Thinking...", expanded=True)
        graph = get_graph()
        try:
            result = _loop().run_until_complete(
                graph.ainvoke({"messages": st.session_state.history})
            )
        except Exception as e:  # noqa: BLE001
            status.update(label="Agent error", state="error", expanded=True)
            msg = str(e)
            if "tool_use_failed" in msg or "was not in request.tools" in msg:
                hint = (
                    "The LLM emitted an invalid tool call. Try rephrasing the "
                    "question, or retry — this is a known limitation."
                )
            elif "rate_limit" in msg.lower():
                hint = "Provider rate limit reached. Try again in a minute, or switch model in .env."
            else:
                hint = "Try again, or check the logs."
            st.error(f"**Agent failed.** {hint}\n\n```\n{msg[:600]}\n```")
            if st.session_state.history and isinstance(st.session_state.history[-1], HumanMessage):
                st.session_state.history.pop()
            return

        new_msgs = result["messages"][len(st.session_state.history) - 1 :]
        for m in new_msgs:
            step = _step_label(m)
            if step:
                kind, body, _ = step
                status.markdown(
                    f"<div class='lf-step'>"
                    f"<span class='lf-step-kind'>{kind}</span>{body}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        status.update(label="Done", state="complete", expanded=False)

    # Each agent message gets its own chat bubble below for clarity.
    agent_msgs = []
    for m in new_msgs:
        if (
            isinstance(m, AIMessage) and m.content and not m.tool_calls
            and not any(s in m.content.lower() for s in HANDOFF_NOISE)
        ):
            with st.chat_message("assistant"):
                name = getattr(m, "name", None) or "supervisor"
                st.markdown(
                    f"<span class='lf-agent-label'>{name.replace('_', ' ')}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(m.content)
            st.session_state.history.append(m)
            agent_msgs.append(m)

    render_trade_actions(agent_msgs)
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
