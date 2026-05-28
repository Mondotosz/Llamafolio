"""LangChain tools exposed to the agents.

- `alpaca_mcp` spawns Alpaca's official MCP server and turns its tools
  into LangChain `BaseTool`s.
- `tavily_search` wraps Tavily's web-search API.
- `yfinance_tools` exposes `get_fundamentals` and `get_company_info`
  for valuation / sector / beta lookups that Alpaca's feed does not
  cover.

The tools are instantiated and bound to specialists in
`llamafolio.agents.graph`; this `__init__` only re-exports the
constructors for convenience.
"""
from llamafolio.tools.alpaca_mcp import get_alpaca_tools
from llamafolio.tools.tavily_search import TAVILY_TOOLS, web_search
from llamafolio.tools.yfinance_tools import (
    YFINANCE_TOOLS,
    get_company_info,
    get_fundamentals,
)

__all__ = [
    "TAVILY_TOOLS",
    "YFINANCE_TOOLS",
    "get_alpaca_tools",
    "get_company_info",
    "get_fundamentals",
    "web_search",
]
