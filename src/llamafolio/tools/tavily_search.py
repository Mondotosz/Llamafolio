"""Tavily web search wrapped as a LangChain tool.

Used for open-ended research questions that the Alpaca news feed can't answer
(macro, regulation, sentiment, sector-wide events, etc.).
"""
from __future__ import annotations

from typing import Any

from langchain_core.tools import tool
from tavily import TavilyClient

from llamafolio.config import load_settings


def _client() -> TavilyClient:
    return TavilyClient(api_key=load_settings().tavily_api_key)


@tool
def web_search(query: str, max_results: int = 5) -> dict[str, Any]:
    """Search the web for recent information. Use for macro context, regulation,
    sentiment, or any question the financial-data tools cannot answer.

    Args:
        query: Natural language search query.
        max_results: Number of results to return (default 5, max 10).
    """
    response = _client().search(
        query=query,
        max_results=min(max_results, 10),
        search_depth="basic",
        include_answer=True,
    )
    return {
        "query": query,
        "answer": response.get("answer"),
        "results": [
            {
                "title": r.get("title"),
                "url": r.get("url"),
                "content": (r.get("content") or "")[:500],
            }
            for r in response.get("results", [])
        ],
    }


TAVILY_TOOLS = [web_search]
