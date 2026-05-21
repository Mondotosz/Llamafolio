"""Smoke test for the single ReAct agent.

Asks one portfolio-analysis question and prints every step (tool calls + final
answer). Useful to confirm the whole stack (Groq + LangGraph + Alpaca MCP +
yfinance + Tavily) works end-to-end.
"""
from __future__ import annotations

import asyncio

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from rich.console import Console
from rich.panel import Panel

from llamafolio.agents.single_agent import build_single_agent

QUESTION = (
    "Take a look at my current Alpaca paper portfolio. "
    "What's my biggest sector exposure, and do you see any concentration risk? "
    "If yes, suggest ONE position to trim — propose the trade but do NOT execute it."
)


def _short(text: str, limit: int = 400) -> str:
    text = str(text)
    return text if len(text) <= limit else text[:limit] + " […]"


async def main() -> None:
    console = Console()
    console.rule("[bold cyan]Building single agent")
    agent = await build_single_agent()

    console.rule("[bold cyan]User question")
    console.print(QUESTION)

    console.rule("[bold cyan]Agent run")
    result = await agent.ainvoke({"messages": [HumanMessage(content=QUESTION)]})

    for msg in result["messages"]:
        if isinstance(msg, HumanMessage):
            console.print(Panel(_short(msg.content), title="user", border_style="blue"))
        elif isinstance(msg, AIMessage):
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    console.print(
                        Panel(
                            f"[bold]{tc['name']}[/bold]\nargs: {tc['args']}",
                            title="tool call",
                            border_style="yellow",
                        )
                    )
            if msg.content:
                console.print(Panel(_short(msg.content, 2000), title="assistant", border_style="green"))
        elif isinstance(msg, ToolMessage):
            console.print(
                Panel(_short(msg.content), title=f"tool result · {msg.name}", border_style="magenta")
            )


if __name__ == "__main__":
    asyncio.run(main())
