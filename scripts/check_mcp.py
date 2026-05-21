"""Smoke test: spawn the Alpaca MCP server and list the tools it exposes."""
from __future__ import annotations

import asyncio

from rich.console import Console
from rich.table import Table

from llamafolio.config import load_settings
from llamafolio.tools.alpaca_mcp import get_alpaca_tools


async def main() -> None:
    console = Console()
    settings = load_settings()

    console.rule("[bold cyan]Connecting to Alpaca MCP server")
    console.print("[dim]Spawning `uvx alpaca-mcp-server` via stdio...[/dim]")
    tools = await get_alpaca_tools(settings)

    console.rule(f"[bold cyan]{len(tools)} tools available")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="green")
    table.add_column("Description")
    for tool in tools:
        desc = (tool.description or "").split("\n", 1)[0]
        table.add_row(tool.name, desc[:90])
    console.print(table)


if __name__ == "__main__":
    asyncio.run(main())
