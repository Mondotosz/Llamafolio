"""Alpaca MCP server integration.

Spawns the official `alpaca-mcp-server` (PyPI) as a stdio subprocess via uvx and
exposes its tools as LangChain `BaseTool` objects through langchain-mcp-adapters.

We default to a restricted toolset (account, trading, stock-data, news) to keep
the agent's context window manageable — the server exposes 60+ tools by default
(crypto, options, watchlists, etc.) which inflates prompts and slows the LLM.

Available toolsets (from the alpaca-mcp-server README):
  account, trading, watchlists, assets, stock-data, crypto-data,
  options-data, corporate-actions, news
"""
from __future__ import annotations

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from llamafolio.config import Settings

DEFAULT_TOOLSETS = "account,trading,stock-data,news"

# Tools we never want in this POC (crypto, options, niche actions). Dropping
# them keeps the system prompt small enough for Groq's free-tier TPM limit.
EXCLUDED_TOOLS = {
    "place_crypto_order",
    "place_option_order",
    "get_crypto_bars",
    "get_crypto_quotes",
    "get_crypto_trades",
    "exercise_options_position",
    "do_not_exercise_options_position",
    "get_order_by_client_id",
    "get_account_config",
    "update_account_config",
    "replace_order_by_id",
    "get_account_activities",
    "get_account_activities_by_type",
}


def build_alpaca_mcp_client(
    settings: Settings,
    toolsets: str = DEFAULT_TOOLSETS,
) -> MultiServerMCPClient:
    """Build (but don't start) a MultiServerMCPClient pointing at Alpaca MCP."""
    return MultiServerMCPClient(
        {
            "alpaca": {
                "transport": "stdio",
                "command": "uvx",
                "args": ["alpaca-mcp-server"],
                "env": {
                    "ALPACA_API_KEY": settings.alpaca_api_key,
                    "ALPACA_SECRET_KEY": settings.alpaca_secret_key,
                    "ALPACA_PAPER_TRADE": "True",
                    "ALPACA_TOOLSETS": toolsets,
                },
            }
        }
    )


async def get_alpaca_tools(
    settings: Settings,
    toolsets: str = DEFAULT_TOOLSETS,
) -> list[BaseTool]:
    """Connect to the Alpaca MCP server and return LangChain tools (filtered)."""
    client = build_alpaca_mcp_client(settings, toolsets=toolsets)
    tools = await client.get_tools()
    return [t for t in tools if t.name not in EXCLUDED_TOOLS]
