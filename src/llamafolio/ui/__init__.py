"""Streamlit UI for Llamafolio.

The package is organised by surface, not by widget kind, so each module
owns one visible chunk of the screen and can be reasoned about in
isolation:

  - assets       : static file paths + base64 helper
  - styles       : the entire stylesheet, written via `inject()`
  - messages     : LangChain message helpers (text extraction, step labels)
  - charts       : Plotly figures (equity sparkline, sector donut)
  - header       : top brand band + 'New conversation' button
  - sidebar      : left-rail portfolio dashboard
  - empty_state  : welcome card + agent grid + suggestion chips
  - trade_detector : parses structured trade proposals from agent output
  - chat         : history replay, streaming turn, trade banner, metrics
  - main         : composes everything; called from app.py at the repo root
"""
from llamafolio.ui.main import main

__all__ = ["main"]
