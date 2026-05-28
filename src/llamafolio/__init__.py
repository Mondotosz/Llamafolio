"""Llamafolio — multi-agent LLM portfolio advisor.

Public API:

    from llamafolio import build_graph, load_settings

`build_graph` returns a compiled LangGraph runnable with the
multi-agent supervisor and the intent router wired together.
`load_settings` returns the typed configuration loaded from `.env`.
"""
from llamafolio.agents import build_graph
from llamafolio.config import load_settings

__all__ = ["build_graph", "load_settings"]
