"""Static asset paths and base64 helper for inline embedding.

The brand kit lives at the repository root under `assets/`. The Streamlit
chat-avatar API accepts a file path directly, but the brand lockup in the
header is injected as a base64 data URI because Streamlit's `st.markdown`
cannot serve a local file from arbitrary HTML.
"""
from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
ASSETS_DIR = REPO_ROOT / "assets"

FAVICON = str(ASSETS_DIR / "favicon-512.png")
ASSISTANT_AVATAR = str(ASSETS_DIR / "llamafolio-icon-premium.png")
USER_AVATAR = str(ASSETS_DIR / "user-avatar.svg")


@st.cache_data
def asset_b64(name: str) -> str:
    """Return a base64 string for the asset named `name` (relative to assets/).

    Cached because each header render would otherwise re-read and re-encode
    the same SVG on every Streamlit script run.
    """
    return base64.b64encode((ASSETS_DIR / name).read_bytes()).decode()
