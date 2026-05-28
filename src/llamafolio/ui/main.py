"""Streamlit UI entry point.

Composes the three rendering sections (sidebar, header, chat) and is
responsible for the one-time `st.set_page_config` call and CSS
injection. Used by the thin `app.py` at the repository root so that
`streamlit run app.py` Just Works.
"""
from __future__ import annotations

import streamlit as st

from llamafolio.ui import chat, header, sidebar, styles
from llamafolio.ui.assets import FAVICON


def main() -> None:
    """Render one full Streamlit script pass."""
    st.set_page_config(
        page_title="Llamafolio",
        page_icon=FAVICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    styles.inject()
    sidebar.render()
    header.render()
    chat.render()
