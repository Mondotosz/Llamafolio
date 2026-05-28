"""Intent router — cheap pre-classifier in front of the multi-agent supervisor.

Most user questions ("what's in my portfolio", "price of NVDA", ...) don't
need the full analyst -> research -> risk chain. Routing them to dedicated
short paths cuts the average LLM round-trip count per turn by ~3-5x.

Paths:
  - data      : 0 LLM calls, just echo the pre-fetched <portfolio_context>
  - analyst   : invoke only the portfolio_analyst subgraph
  - research  : invoke only the research_agent subgraph
  - risk      : invoke only the risk_manager subgraph
  - complex   : fall back to the existing supervisor chain
  - executor  : invoke only the executor (after explicit confirmation)
  - decline   : polite refusal, no LLM call

Only the classifier itself costs an extra small LLM call; the simple paths
save 4-6 round-trips compared to going through the supervisor every time.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated, Any, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
VALID_INTENTS = {
    "data", "analyst", "research", "risk", "complex", "executor", "decline",
}


class RouterState(TypedDict):
    """State threaded through the router graph.

    `messages` is the standard LangChain message channel; `intent` is set
    by the classifier and read by the conditional edge.
    """
    messages: Annotated[list[BaseMessage], add_messages]
    intent: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _content_text(m: Any) -> str:
    """Extract text from a message whose content might be str OR list of parts."""
    c = getattr(m, "content", "") or ""
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts: list[str] = []
        for chunk in c:
            if isinstance(chunk, str):
                parts.append(chunk)
            elif isinstance(chunk, dict):
                t = chunk.get("text") or chunk.get("content") or ""
                if isinstance(t, str):
                    parts.append(t)
        return "".join(parts)
    return str(c)


def _last_human_text(messages: list[BaseMessage]) -> str:
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            return _content_text(m)
    return ""


def _extract_portfolio_context(text: str) -> str | None:
    """Pull the <portfolio_context>...</portfolio_context> block injected by
    app.py at the start of the user message, if any."""
    m = re.search(r"<portfolio_context>(.*?)</portfolio_context>", text, re.DOTALL)
    return m.group(1).strip() if m else None


def _strip_context(text: str) -> str:
    """Return the user's *original* question with the auto-context removed."""
    text = re.sub(r"<portfolio_context>.*?</portfolio_context>", "", text, flags=re.DOTALL)
    text = re.sub(r"User question:\s*", "", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------
def make_classifier_node(llm: BaseChatModel):
    """Single small LLM call that picks one of VALID_INTENTS."""
    classifier_prompt = (PROMPTS_DIR / "intent_router.md").read_text(encoding="utf-8")

    async def classifier(state: RouterState) -> dict:
        question = _strip_context(_last_human_text(state["messages"]))
        if not question:
            return {"intent": "decline"}

        # Cheap deterministic shortcut: confirmation phrases skip the
        # classifier LLM entirely. Verbose Gemini outputs sometimes returned
        # 'The intent is executor.' which broke the first-token parser and
        # fell back to the expensive 'complex' chain when a single executor
        # call was all we needed.
        low = question.lower().strip()
        if low.startswith(("confirm ", "execute ", "yes, ")) and any(
            k in low for k in ("sell", "buy", "trim")
        ):
            return {"intent": "executor"}

        response = await llm.ainvoke([
            SystemMessage(content=classifier_prompt),
            HumanMessage(content=question),
        ])
        raw = _content_text(response).strip().lower()
        # Robust parser: search the full response for any valid intent word,
        # not just the first token. Gemini Flash Lite occasionally wraps the
        # answer in a short sentence rather than emitting one bare word.
        for candidate in VALID_INTENTS:
            if re.search(rf"\b{candidate}\b", raw):
                return {"intent": candidate}
        return {"intent": "complex"}

    return classifier


async def data_node(state: RouterState) -> dict:
    """No-LLM path: render the pre-fetched portfolio context as the answer."""
    ctx = _extract_portfolio_context(_last_human_text(state["messages"]))
    if ctx:
        body = (
            "Here is your current portfolio snapshot:\n\n"
            + ctx
            + "\n\nAsk me to *analyse* it, *research* a position, or *suggest a trim* "
            "and I'll route the question to the right specialist."
        )
    else:
        body = "I couldn't pull your portfolio data right now. Try again in a moment."
    return {"messages": [AIMessage(content=body, name="supervisor")]}


async def decline_node(state: RouterState) -> dict:
    """Polite refusal for out-of-scope questions, no LLM call."""
    body = (
        "I'm focused on your Alpaca paper portfolio — analysis, research on "
        "your positions, risk checks and trade execution. I can't help with "
        "that. Try asking about your holdings, sector exposure, or a specific "
        "ticker."
    )
    return {"messages": [AIMessage(content=body, name="supervisor")]}


def make_specialist_node(specialist):
    """Wrap a compiled react-agent subgraph as a router node."""

    async def node(state: RouterState) -> dict:
        result = await specialist.ainvoke({"messages": state["messages"]})
        return {"messages": result["messages"]}

    return node


def make_complex_node(supervisor_graph):
    """Fall-back path: run the existing supervisor chain unchanged."""

    async def node(state: RouterState) -> dict:
        result = await supervisor_graph.ainvoke({"messages": state["messages"]})
        return {"messages": result["messages"]}

    return node


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------
def build_router_graph(
    llm: BaseChatModel,
    *,
    analyst,
    research,
    risk,
    executor,
    supervisor_graph,
):
    """Compile the router graph that sits in front of the supervisor chain."""
    workflow = StateGraph(RouterState)

    workflow.add_node("classifier", make_classifier_node(llm))
    workflow.add_node("data", data_node)
    workflow.add_node("decline", decline_node)
    workflow.add_node("analyst", make_specialist_node(analyst))
    workflow.add_node("research", make_specialist_node(research))
    workflow.add_node("risk", make_specialist_node(risk))
    workflow.add_node("executor", make_specialist_node(executor))
    workflow.add_node("complex", make_complex_node(supervisor_graph))

    workflow.set_entry_point("classifier")
    workflow.add_conditional_edges(
        "classifier",
        lambda state: state["intent"],
        {
            "data": "data",
            "analyst": "analyst",
            "research": "research",
            "risk": "risk",
            "executor": "executor",
            "complex": "complex",
            "decline": "decline",
        },
    )

    for terminal in ("data", "decline", "analyst", "research", "risk", "executor", "complex"):
        workflow.add_edge(terminal, END)

    return workflow.compile()
