"""Welcome card, specialist agent grid, and suggestion chips.

The empty state is what the user sees before sending their first
question of the conversation. It explains how the system works (one
short paragraph + a four-step "how a turn flows" mini-list) and shows
the four specialist agents as a card grid so the user knows what the
system can do.

The suggestion chips are rendered both in the empty state and
persistently above the chat input once the conversation has started.
They use Streamlit's `on_click` callback pattern so the click reliably
fires the next turn even when rendered at the end of a streaming
response.
"""
from __future__ import annotations

import streamlit as st


AGENTS = (
    {
        "name": "portfolio_analyst",
        "role": "Reads your portfolio",
        "desc": (
            "Computes composition, sector exposure on invested capital, "
            "and flags concentration above 40%."
        ),
    },
    {
        "name": "research_agent",
        "role": "Gathers context",
        "desc": (
            "Pulls news, snapshots, fundamentals and web sources to back "
            "any claim with citations."
        ),
    },
    {
        "name": "risk_manager",
        "role": "Vets every proposal",
        "desc": (
            "Checks position sizing, sector exposure post-trade and "
            "volatility before any trade idea reaches you."
        ),
    },
    {
        "name": "executor",
        "role": "Places paper orders",
        "desc": (
            "Only invoked after you explicitly confirm. Refuses ambiguous "
            "instructions on purpose."
        ),
    },
)


SUGGESTIONS = (
    (
        "Analyse my sector exposure",
        "Analyse my sector exposure and flag any concentration risk.",
    ),
    (
        "Recent news on my holdings",
        "Summarise recent news on each of my current holdings.",
    ),
    (
        "Suggest a rebalancing",
        "Suggest ONE position to trim with research and a risk check. Do not execute.",
    ),
    (
        "Account snapshot",
        "Give me a one-paragraph snapshot of my account state.",
    ),
)


def render_welcome() -> None:
    """Render the welcome card + how-it-works + agent grid."""
    st.markdown(
        """
        <div class="lf-hero-block">
          <div class="lf-intro">
            <h2>Ask anything about your portfolio</h2>
            <p>Llamafolio routes your question across four specialist agents,
            then synthesises a single answer with sources. Trades are
            <strong>never</strong> executed without your explicit
            confirmation &mdash; you get a confirm/refuse button when an
            order is proposed.</p>
          </div>
          <div class="lf-flow">
            <div class="lf-flow-title">How a turn flows</div>
            <div class="lf-flow-step">
              <span class="lf-flow-num">1</span> Supervisor reads the question
            </div>
            <div class="lf-flow-step">
              <span class="lf-flow-num">2</span> Routes to the right specialist(s)
            </div>
            <div class="lf-flow-step">
              <span class="lf-flow-num">3</span> Specialists call MCP &amp; web tools
            </div>
            <div class="lf-flow-step">
              <span class="lf-flow-num">4</span> Supervisor synthesises and ends
            </div>
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
    st.markdown(
        f"<div class='lf-agent-grid'>{cards_html}</div>",
        unsafe_allow_html=True,
    )


def _set_pending(query: str) -> None:
    st.session_state["pending_input"] = query


def render_suggestions(key_prefix: str = "sug") -> None:
    """Render one row of quick-prompt chip buttons."""
    cols = st.columns(len(SUGGESTIONS))
    for col, (label, query) in zip(cols, SUGGESTIONS):
        col.button(
            label,
            use_container_width=True,
            key=f"{key_prefix}_{label}",
            on_click=_set_pending,
            args=(query,),
        )
