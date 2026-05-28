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

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
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

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def _by_name(tools: list[BaseTool], names: list[str]) -> list[BaseTool]:
    """Pick MCP tools by name, silently skipping any that aren't present."""
    by_name = {t.name: t for t in tools}
    return [by_name[n] for n in names if n in by_name]


def build_llm(settings: Settings) -> BaseChatModel:
    """Build the LLM, dispatching on settings.llm_provider.

    Both providers are wrapped through the standard LangChain chat-model
    interface so the rest of the graph stays agnostic. We deliberately do
    NOT wrap with `.with_retry(...)` — that would return a Runnable that
    lacks `bind_tools()`, which `create_react_agent` needs. Each SDK
    already retries 429s internally; we just bump max_retries.
    """
    if settings.llm_provider == "groq":
        if not settings.groq_api_key:
            raise RuntimeError(
                "LLM_PROVIDER=groq but GROQ_API_KEY is missing from the .env."
            )
        return ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0.1,
            max_retries=5,
        )
    if settings.llm_provider == "gemini":
        if not settings.google_api_key:
            raise RuntimeError(
                "LLM_PROVIDER=gemini but GOOGLE_API_KEY is missing from the .env. "
                "Get a free key at https://aistudio.google.com/apikey"
            )
        # thinking_budget=0 disables Gemini 2.5's thinking mode. We MUST do
        # this for langgraph-supervisor: thinking models require every prior
        # functionCall in the conversation to carry a 'thought_signature',
        # but the supervisor synthesises handoff tool calls
        # (transfer_to_*, transfer_back_to_supervisor) without one, which
        # makes Gemini reject the next request with 400 INVALID_ARGUMENT.
        # Disabling thinking sidesteps the signature requirement.
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=0.1,
            max_retries=5,
            thinking_budget=0,
        )
    raise RuntimeError(f"Unknown LLM provider: {settings.llm_provider!r}")


# Backwards-compat alias used elsewhere in this module.
_llm = build_llm


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

    # --- supervisor (fallback for complex multi-step requests) -------------
    # output_mode="full_history" bubbles every sub-agent message (tool calls,
    # tool results, reasoning) up to the parent state. We rely on this in two
    # places:
    #   - the eval harness extracts the set of tools that were actually
    #     called, which is only visible when the sub-agent messages are
    #     preserved;
    #   - the Streamlit timeline shows the real chain of tool calls per
    #     specialist instead of just the handoff transitions.
    supervisor_compiled = create_supervisor(
        agents=[analyst, research, risk, executor],
        model=llm,
        prompt=_prompt("supervisor"),
        output_mode="full_history",
    ).compile()

    # --- router (cheap classifier that shortcuts to the simplest path) -----
    # For most user questions (data display, single-specialist needs, polite
    # decline) we bypass the supervisor entirely and route directly to the
    # right node. Only multi-step decisions (trim, rebalance, recommend) fall
    # through to the supervisor chain. See agents/router.py for the path map.
    from llamafolio.agents.router import build_router_graph
    return build_router_graph(
        llm,
        analyst=analyst,
        research=research,
        risk=risk,
        executor=executor,
        supervisor_graph=supervisor_compiled,
    )


# Convenience export -- unused tool lists kept for ad-hoc imports/tests
__all__ = ["build_graph", "YFINANCE_TOOLS", "TAVILY_TOOLS"]
