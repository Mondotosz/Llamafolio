"""Chat surface — history replay, streaming turn, trade banner and metrics.

This module owns the central column of the app: the conversation
history, the live agent timeline and bubbles produced during streaming,
the structured trade-confirmation banner, and the per-turn metrics
footer.

The runtime glue (persistent asyncio event loop + cached compiled
LangGraph) also lives here because it is only ever used by the
streaming turn.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from llamafolio.agents.graph import build_graph
from llamafolio.config import load_settings
from llamafolio.data import (
    load_account,
    load_equity_history,
    load_positions,
    render_portfolio_context,
)
from llamafolio.ui.assets import ASSISTANT_AVATAR, USER_AVATAR
from llamafolio.ui.empty_state import render_suggestions, render_welcome
from llamafolio.ui.messages import HANDOFF_NOISE, content_text, step_label
from llamafolio.ui.trade_detector import detect_proposed_trade


# ---------------------------------------------------------------------------
# Runtime glue — persistent event loop + cached graph
# ---------------------------------------------------------------------------
def _loop() -> asyncio.AbstractEventLoop:
    """One asyncio loop per Streamlit session.

    The compiled LangGraph and its MCP stdio connections are bound to
    the loop that built them; reusing the same loop on every turn keeps
    those connections alive.
    """
    if "_loop" not in st.session_state:
        st.session_state["_loop"] = asyncio.new_event_loop()
    return st.session_state["_loop"]


@st.cache_resource(show_spinner="Booting agents and Alpaca MCP server...")
def _get_graph():
    return _loop().run_until_complete(build_graph())


# ---------------------------------------------------------------------------
# Trade confirmation banner
# ---------------------------------------------------------------------------
def _render_trade_actions(agent_msgs: list[Any]) -> None:
    """Surface a Confirm / Refuse pair when this turn contains a proposal.

    Guarded by two conditions:
      1. If the executor has already reported an order placed / accepted
         in this turn, the loop is closed — no banner.
      2. The executor's own success block echoes the symbol/side/qty,
         so we skip it while scanning so it cannot trigger the banner.
    """
    # 1) Loop closed: executor already placed an order this turn.
    for m in agent_msgs:
        if getattr(m, "name", None) == "executor":
            text_low = content_text(m).lower()
            if "order placed" in text_low or "accepted" in text_low:
                return

    # 2) Find a proposal among non-executor messages.
    trade: dict | None = None
    for m in agent_msgs:
        if getattr(m, "name", None) == "executor":
            continue
        trade = detect_proposed_trade(content_text(m))
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

    # on_click callbacks rather than `if st.button: st.rerun()` —
    # callbacks fire BEFORE Streamlit's natural rerun and are robust to
    # being rendered at the very end of a streaming turn.
    def _confirm() -> None:
        st.session_state["pending_input"] = (
            f"confirm {trade['side']} {trade['symbol']} {trade['qty']}"
        )

    def _refuse() -> None:
        st.session_state["pending_input"] = (
            f"do not execute the proposed {trade['side']} of "
            f"{trade['symbol']}. close the loop."
        )

    c1, c2, _ = st.columns([1, 1, 4])
    c1.button(
        "Confirm",
        type="primary",
        key=f"confirm_{trade['symbol']}",
        width="stretch",
        on_click=_confirm,
    )
    c2.button(
        "Refuse",
        key=f"refuse_{trade['symbol']}",
        width="stretch",
        on_click=_refuse,
    )


# ---------------------------------------------------------------------------
# Per-turn metrics footer
# ---------------------------------------------------------------------------
def _render_metrics_footer(
    metrics: dict[str, Any], elapsed_s: float
) -> None:
    n_specialists = len(metrics["agents"] - {"supervisor"})
    st.markdown(
        f"<div class='lf-metrics'>"
        f"<span class='lf-metric-chip'><b>{n_specialists}</b>specialists</span>"
        f"<span class='lf-metric-chip'><b>{metrics['tool_calls']}</b>tool calls</span>"
        f"<span class='lf-metric-chip'><b>{metrics['llm_calls']}</b>LLM round-trips</span>"
        f"<span class='lf-metric-chip'><b>{elapsed_s:.1f}s</b>total</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Streaming turn
# ---------------------------------------------------------------------------
def _wrap_prompt_with_portfolio_context(prompt: str) -> str:
    """Inline a fresh portfolio snapshot into the user's question.

    This is the core cost optimisation: one Alpaca read on the host fills
    the LLM's context with everything the analyst would otherwise fetch
    via 10+ MCP tool round-trips. Returns the raw prompt unchanged if the
    snapshot cannot be loaded.
    """
    settings = load_settings()
    try:
        ctx = render_portfolio_context(
            load_account(settings),
            load_positions(settings),
            load_equity_history(settings, period="1D", timeframe="1Min"),
        )
        return f"{ctx}\n\nUser question: {prompt}"
    except Exception:  # noqa: BLE001
        return prompt


def _format_error(err: str) -> str:
    if "tool_use_failed" in err or "was not in request.tools" in err:
        return (
            "The LLM emitted an invalid tool call. Try rephrasing the "
            "question, or retry — this is a known limitation."
        )
    if "rate_limit" in err.lower() or "resource_exhausted" in err.lower():
        return (
            "Provider rate limit reached. Try again in a minute, "
            "or switch model in .env."
        )
    return "Try again, or check the logs."


def _stream_turn(prompt: str) -> None:
    """Run one chat turn end-to-end: render the user bubble, drive the
    graph, stream agent bubbles + timeline, then surface the banner +
    metrics footer."""
    # 1) Persist the original prompt in history and echo it as a bubble.
    st.session_state.history.append(HumanMessage(content=prompt))
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    # 2) Build the message list with portfolio context wrapped in the
    #    *last* user message; older history stays unwrapped for display.
    wrapped_prompt = _wrap_prompt_with_portfolio_context(prompt)
    message_list = [
        *st.session_state.history[:-1],
        HumanMessage(content=wrapped_prompt),
    ]

    loop = _loop()
    graph = _get_graph()
    status = st.status("Thinking...", expanded=True)

    agent_msgs: list[Any] = []
    seen_ids: set[str] = set()
    input_msg_ids: set = {
        getattr(m, "id", None)
        for m in message_list
        if getattr(m, "id", None)
    }
    metrics: dict[str, Any] = {
        "agents": set(),
        "tool_calls": 0,
        "llm_calls": 0,
    }
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

            for _node_name, node_state in chunk.items():
                if not isinstance(node_state, dict):
                    continue
                for m in node_state.get("messages", []):
                    msg_id = getattr(m, "id", None) or str(id(m))
                    if msg_id in seen_ids:
                        continue
                    seen_ids.add(msg_id)

                    # Subgraphs re-emit history as part of their updates.
                    # Skip anything we already had in the input so the
                    # metrics counter and the chat bubbles only reflect
                    # this turn's real work.
                    if msg_id in input_msg_ids:
                        continue

                    if isinstance(m, AIMessage):
                        metrics["llm_calls"] += 1
                        name = getattr(m, "name", None)
                        if name:
                            metrics["agents"].add(name)
                        for tc in m.tool_calls or []:
                            t = tc["name"]
                            if not (
                                t.startswith("transfer_to_")
                                or t.startswith("transfer_back")
                            ):
                                metrics["tool_calls"] += 1

                    step = step_label(m)
                    if step:
                        kind, body = step
                        status.markdown(
                            f"<div class='lf-step'>"
                            f"<span class='lf-step-kind'>{kind}</span>{body}"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                    text = content_text(m)
                    if (
                        isinstance(m, AIMessage)
                        and text
                        and not m.tool_calls
                        and not any(s in text.lower() for s in HANDOFF_NOISE)
                    ):
                        with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
                            name = getattr(m, "name", None) or "supervisor"
                            st.markdown(
                                f"<span class='lf-agent-label'>"
                                f"{name.replace('_', ' ')}</span>",
                                unsafe_allow_html=True,
                            )
                            st.markdown(text)
                        st.session_state.history.append(m)
                        agent_msgs.append(m)
    except Exception as e:  # noqa: BLE001
        status.update(label="Agent error", state="error", expanded=True)
        err = str(e)
        st.error(
            f"**Agent failed.** {_format_error(err)}\n\n```\n{err[:600]}\n```"
        )
        # Roll back so the next turn starts from a clean history.
        if (
            st.session_state.history
            and isinstance(st.session_state.history[-1], HumanMessage)
        ):
            st.session_state.history.pop()
        return
    finally:
        status.update(label="Done", state="complete", expanded=False)

    _render_trade_actions(agent_msgs)
    _render_metrics_footer(metrics, time.perf_counter() - t_start)
    st.markdown(
        "<div class='lf-disclaimer'>Paper trading account &middot; "
        "informational only &middot; not investment advice.</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Top-level chat renderer
# ---------------------------------------------------------------------------
def render() -> None:
    """Render the chat column: welcome, history, input, streaming."""
    if "history" not in st.session_state:
        st.session_state.history = []

    # Welcome state: shown only before the first human message of the
    # conversation. Once the user has spoken, the chips move below the
    # input so they remain reachable as quick prompts.
    show_welcome = not any(
        isinstance(m, HumanMessage) for m in st.session_state.history
    )
    if show_welcome:
        render_welcome()
        render_suggestions("welcome")

    # Replay history.
    for msg in st.session_state.history:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user", avatar=USER_AVATAR):
                st.markdown(content_text(msg))
        elif (
            isinstance(msg, AIMessage)
            and content_text(msg)
            and not msg.tool_calls
        ):
            with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
                name = getattr(msg, "name", None) or "supervisor"
                st.markdown(
                    f"<span class='lf-agent-label'>"
                    f"{name.replace('_', ' ')}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(content_text(msg))

    # Pending input either from a chip click (last rerun) or a fresh
    # st.chat_input submission this run.
    typed = st.chat_input("Ask anything about your portfolio.")
    pending = st.session_state.pop("pending_input", None)
    prompt = pending or typed

    # Persistent quick prompts under the input, only after welcome is
    # gone (otherwise the chips are already shown above).
    if not show_welcome:
        st.markdown(
            "<div class='lf-section'>Quick prompts</div>",
            unsafe_allow_html=True,
        )
        render_suggestions("persist")

    if prompt:
        _stream_turn(prompt)
