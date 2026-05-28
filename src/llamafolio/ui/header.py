"""Top brand header (logo + status pill + 'New conversation' button)."""
from __future__ import annotations

import streamlit as st

from llamafolio.config import load_settings
from llamafolio.ui.assets import asset_b64


def _model_label(settings) -> str:
    if settings.llm_provider == "gemini":
        return f"{settings.gemini_model} on Gemini"
    return f"{settings.groq_model} on Groq"


def _clear_conversation() -> None:
    st.session_state["history"] = []
    st.session_state.pop("pending_input", None)


def render() -> None:
    """Render the top brand band: lockup, status pill, action button."""
    lockup_b64 = asset_b64("llamafolio-horizontal-dark.svg")
    settings = load_settings()
    label = _model_label(settings)

    col_brand, col_pill, col_actions = st.columns(
        [3, 2, 1], gap="medium", vertical_alignment="center"
    )
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
            f"Paper &middot; {label}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_actions:
        st.button(
            "New conversation",
            help="Clear the conversation",
            use_container_width=True,
            on_click=_clear_conversation,
        )
    st.markdown(
        "<hr style='margin: 0.5rem 0 1.5rem 0; "
        "border: none; border-top: 1px solid var(--border);'/>",
        unsafe_allow_html=True,
    )
