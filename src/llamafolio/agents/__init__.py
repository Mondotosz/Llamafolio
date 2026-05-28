"""Agentic core — supervisor pattern, intent router and specialists.

`build_graph` is the public entry point: it spawns the Alpaca MCP
server, wires the four specialists (analyst, research, risk, executor)
around the supervisor, puts the intent router in front of the whole
thing, and returns a compiled LangGraph runnable with `.ainvoke` /
`.astream`.
"""
from llamafolio.agents.graph import build_graph, build_llm

__all__ = ["build_graph", "build_llm"]
