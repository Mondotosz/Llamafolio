"""Single ReAct agent — fallback / baseline before the multi-agent split.

One LLM, all tools (Alpaca MCP + yfinance + Tavily), in a ReAct loop built with
LangGraph's prebuilt `create_react_agent`.
"""
from __future__ import annotations

from pathlib import Path

from langchain_core.tools import BaseTool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from llamafolio.config import Settings, load_settings
from llamafolio.tools.alpaca_mcp import get_alpaca_tools
from llamafolio.tools.tavily_search import TAVILY_TOOLS
from llamafolio.tools.yfinance_tools import YFINANCE_TOOLS

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "single_agent.md"


def load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def build_llm(settings: Settings) -> ChatGroq:
    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0.2,
    )


async def collect_tools(settings: Settings) -> list[BaseTool]:
    """All tools the single agent can call."""
    alpaca = await get_alpaca_tools(settings)
    return [*alpaca, *YFINANCE_TOOLS, *TAVILY_TOOLS]


async def build_single_agent(settings: Settings | None = None):
    """Build a ReAct agent with the full toolkit. Returns a LangGraph runnable."""
    settings = settings or load_settings()
    llm = build_llm(settings)
    tools = await collect_tools(settings)
    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=load_system_prompt(),
    )
