"""Multi-agent portfolio advisor graph.

`build_graph()` returns a compiled LangGraph runnable made of two layers:

  1. An intent router (`llamafolio.agents.router`) sits in front and
     classifies each user turn into one of seven paths — data, analyst,
     research, risk, executor, complex or decline. Simple paths bypass
     the supervisor entirely.
  2. A `langgraph-supervisor` chain wires the four specialists for the
     'complex' fallback path:
       - supervisor       : routes between specialists, never calls tools
       - portfolio_analyst: reads positions, sector exposure, concentration
       - research_agent   : news, fundamentals, market context, web search
       - risk_manager     : vol / beta / exposure check on a proposed trade
       - executor         : places / cancels / closes orders (only after
                            the user explicitly confirms a structured proposal)

Each specialist receives a focused subset of tools — keeping individual
prompts small enough to fit the free-tier token-per-minute caps on both
Groq and Gemini.
"""
from __future__ import annotations

import logging
from pathlib import Path

from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from llamafolio.agents.router import build_router_graph
from llamafolio.config import Settings, load_settings
from llamafolio.tools.alpaca_mcp import get_alpaca_tools
from llamafolio.tools.tavily_search import web_search
from llamafolio.tools.yfinance_tools import get_company_info, get_fundamentals

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
    if settings.llm_provider == "ollama":
        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.1,
            reasoning=False,  # disable thinking mode — same incompatibility with langgraph-supervisor as Gemini 2.5
        )
    raise RuntimeError(f"Unknown LLM provider: {settings.llm_provider!r}")


async def build_graph(settings: Settings | None = None):
    """Build the multi-agent graph + router. Returns a compiled LangGraph app."""
    settings = settings or load_settings()
    if settings.llm_provider == "gemini":
        model = settings.gemini_model
    elif settings.llm_provider == "ollama":
        model = settings.ollama_model
    else:
        model = settings.groq_model
    logger.info("Building graph: provider=%s model=%s", settings.llm_provider, model)
    llm = build_llm(settings)
    alpaca = await get_alpaca_tools(settings)
    logger.info("Alpaca MCP tools loaded: %d tools available", len(alpaca))

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
    # The executor is intentionally NOT in the supervisor's agent list. The
    # supervisor's job is to PROPOSE a trade (structured **Proposed trade**
    # block); execution only happens after explicit user confirmation, which
    # the router catches and routes to the guarded executor node. Without
    # this exclusion, the supervisor could chain analyst -> research -> risk
    # -> executor autonomously, bypassing the structural proposal guard.
    # Discovered by the adversarial-prompt-injection-via-news-question case.
    #
    # output_mode="full_history" bubbles every sub-agent message (tool calls,
    # tool results, reasoning) up to the parent state. We rely on this in two
    # places:
    #   - the eval harness extracts the set of tools that were actually
    #     called, which is only visible when the sub-agent messages are
    #     preserved;
    #   - the Streamlit timeline shows the real chain of tool calls per
    #     specialist instead of just the handoff transitions.
    supervisor_compiled = create_supervisor(
        agents=[analyst, research, risk],
        model=llm,
        prompt=_prompt("supervisor"),
        output_mode="full_history",
    ).compile()

    # --- router (cheap classifier that shortcuts to the simplest path) -----
    # For most user questions (data display, single-specialist needs, polite
    # decline) we bypass the supervisor entirely and route directly to the
    # right node. Only multi-step decisions (trim, rebalance, recommend) fall
    # through to the supervisor chain. See agents/router.py for the path map.
    graph = build_router_graph(
        llm,
        analyst=analyst,
        research=research,
        risk=risk,
        executor=executor,
        supervisor_graph=supervisor_compiled,
    )
    logger.info("Graph compiled and ready")
    return graph


__all__ = ["build_graph", "build_llm"]
