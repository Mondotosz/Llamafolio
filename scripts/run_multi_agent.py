"""Smoke test for the multi-agent supervisor graph.

Prints every step (routing decisions + sub-agent tool calls + final answer).
"""
from __future__ import annotations

import asyncio

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from rich.console import Console
from rich.panel import Panel

from llamafolio.agents.graph import build_graph

QUESTION = (
    "Take a look at my Alpaca paper portfolio. "
    "Compute my sector exposure and flag any concentration risk. "
    "If there's a problem, propose ONE position to trim with research and a risk check — "
    "but do NOT execute any trade."
)


def _short(text: str, limit: int = 500) -> str:
    text = str(text)
    return text if len(text) <= limit else text[:limit] + " […]"


def _print_message(console: Console, msg) -> None:
    if isinstance(msg, HumanMessage):
        console.print(Panel(_short(msg.content), title="user", border_style="blue"))
    elif isinstance(msg, AIMessage):
        name = getattr(msg, "name", None) or "assistant"
        if msg.tool_calls:
            for tc in msg.tool_calls:
                console.print(
                    Panel(
                        f"[bold]{tc['name']}[/bold]\nargs: {tc['args']}",
                        title=f"{name} → tool call",
                        border_style="yellow",
                    )
                )
        if msg.content:
            console.print(
                Panel(_short(msg.content, 2000), title=name, border_style="green")
            )
    elif isinstance(msg, ToolMessage):
        console.print(
            Panel(_short(msg.content), title=f"tool result · {msg.name}", border_style="magenta")
        )


async def main() -> None:
    console = Console()
    console.rule("[bold cyan]Building multi-agent graph")
    app = await build_graph()

    console.rule("[bold cyan]User question")
    console.print(QUESTION)

    console.rule("[bold cyan]Run")
    result = await app.ainvoke({"messages": [HumanMessage(content=QUESTION)]})
    for msg in result["messages"]:
        _print_message(console, msg)


if __name__ == "__main__":
    asyncio.run(main())
