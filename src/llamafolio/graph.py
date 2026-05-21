"""Multi-agent portfolio advisor graph (supervisor pattern).

Five agents:
  - supervisor: routes the conversation, never calls tools
  - portfolio_analyst: reads positions, sector exposure, concentration
  - research_agent: news, fundamentals, market context, web search
  - risk_manager: vol/beta/exposure check on a proposed trade
  - executor: places/cancels/closes orders (only after explicit confirmation)

Each specialist gets a focused subset of tools to keep its prompt small —
which keeps us under Groq's free-tier TPM ceiling.
"""
from __future__ import annotations

from pathlib import Path

from langchain_core.tools import BaseTool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from llamafolio.config import Settings, load_settings
from llamafolio.tools.alpaca_mcp import get_alpaca_tools
from llamafolio.tools.tavily_search import TAVILY_TOOLS, web_search
from llamafolio.tools.yfinance_tools import (
    YFINANCE_TOOLS,
    get_company_info,
    get_fundamentals,
)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def _by_name(tools: list[BaseTool], names: list[str]) -> list[BaseTool]:
    """Pick MCP tools by name, silently skipping any that aren't present."""
    by_name = {t.name: t for t in tools}
    return [by_name[n] for n in names if n in by_name]


def _llm(settings: Settings) -> ChatGroq:
    """Build the LLM with bumped retry budget for transient Groq rate limits.

    Groq's free tier enforces a per-minute token budget (8k–12k TPM
    depending on the model). The underlying Groq SDK already retries 429s
    with exponential backoff; we bump `max_retries` from the default of 2
    to 5 so a multi-agent run can absorb a couple of TPM hits per turn.

    Note: we deliberately do NOT wrap the model with `.with_retry(...)` —
    that would return a Runnable that lacks `bind_tools()`, which
    `create_react_agent` needs.
    """
    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0.1,
        max_retries=5,
    )


async def build_graph(settings: Settings | None = None):
    """Build the multi-agent supervisor graph. Returns a compiled LangGraph app."""
    settings = settings or load_settings()
    llm = _llm(settings)
    alpaca = await get_alpaca_tools(settings)

    # --- specialists --------------------------------------------------------
    analyst = create_react_agent(
        model=llm,
        tools=[
            *_by_name(alpaca, [
                "get_all_positions",
                "get_open_position",
                "get_account_info",
            ]),
            get_fundamentals,
        ],
        prompt=_prompt("analyst"),
        name="portfolio_analyst",
    )

    research = create_react_agent(
        model=llm,
        tools=[
            *_by_name(alpaca, [
                "get_news",
                "get_stock_snapshot",
                "get_stock_latest_quote",
                "get_market_movers",
                "get_most_active_stocks",
            ]),
            get_fundamentals,
            get_company_info,
            web_search,
        ],
        prompt=_prompt("research"),
        name="research_agent",
    )

    risk = create_react_agent(
        model=llm,
        tools=[
            *_by_name(alpaca, [
                "get_all_positions",
                "get_stock_bars",
            ]),
            get_fundamentals,
        ],
        prompt=_prompt("risk"),
        name="risk_manager",
    )

    executor = create_react_agent(
        model=llm,
        tools=_by_name(alpaca, [
            "place_stock_order",
            "get_orders",
            "get_order_by_id",
            "cancel_order_by_id",
            "cancel_all_orders",
            "close_position",
            "close_all_positions",
            "get_open_position",
            "get_account_info",
        ]),
        prompt=_prompt("executor"),
        name="executor",
    )

    # --- supervisor ---------------------------------------------------------
    # output_mode="full_history" bubbles every sub-agent message (tool calls,
    # tool results, reasoning) up to the parent state. We rely on this in two
    # places:
    #   - the eval harness extracts the set of tools that were actually
    #     called, which is only visible when the sub-agent messages are
    #     preserved;
    #   - the Streamlit timeline shows the real chain of tool calls per
    #     specialist instead of just the handoff transitions.
    supervisor = create_supervisor(
        agents=[analyst, research, risk, executor],
        model=llm,
        prompt=_prompt("supervisor"),
        output_mode="full_history",
    )
    return supervisor.compile()


# Convenience export -- unused tool lists kept for ad-hoc imports/tests
__all__ = ["build_graph", "YFINANCE_TOOLS", "TAVILY_TOOLS"]
