"""Smoke test for yfinance and Tavily tools."""
from __future__ import annotations

from rich.console import Console
from rich.pretty import pprint

from llamafolio.tools.tavily_search import web_search
from llamafolio.tools.yfinance_tools import get_company_info, get_fundamentals


def main() -> None:
    console = Console()

    console.rule("[bold cyan]yfinance — fundamentals for NVDA")
    pprint(get_fundamentals.invoke({"symbol": "NVDA"}))

    console.rule("[bold cyan]yfinance — company info for JPM")
    pprint(get_company_info.invoke({"symbol": "JPM"}))

    console.rule("[bold cyan]Tavily — web search")
    pprint(
        web_search.invoke(
            {"query": "outlook for US semiconductor sector 2026", "max_results": 3}
        )
    )


if __name__ == "__main__":
    main()
