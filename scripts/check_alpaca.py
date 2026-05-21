"""Smoke test: connect to Alpaca paper trading and print account + positions."""
from alpaca.trading.client import TradingClient
from rich.console import Console
from rich.table import Table

from llamafolio.config import load_settings


def main() -> None:
    console = Console()
    settings = load_settings()

    client = TradingClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
        paper=True,
    )

    account = client.get_account()
    console.rule("[bold cyan]Alpaca Paper Account")
    console.print(f"Account ID    : {account.id}")
    console.print(f"Status        : {account.status}")
    console.print(f"Cash          : ${float(account.cash):,.2f}")
    console.print(f"Portfolio val : ${float(account.portfolio_value):,.2f}")
    console.print(f"Buying power  : ${float(account.buying_power):,.2f}")

    positions = client.get_all_positions()
    console.rule("[bold cyan]Positions")
    if not positions:
        console.print("[yellow]No open positions. Run scripts/seed_portfolio.py to seed one.")
        return

    table = Table(show_header=True, header_style="bold magenta")
    for col in ("Symbol", "Qty", "Avg entry", "Current", "Market value", "P/L %"):
        table.add_column(col)
    for p in positions:
        table.add_row(
            p.symbol,
            str(p.qty),
            f"${float(p.avg_entry_price):.2f}",
            f"${float(p.current_price):.2f}",
            f"${float(p.market_value):,.2f}",
            f"{float(p.unrealized_plpc) * 100:+.2f}%",
        )
    console.print(table)


if __name__ == "__main__":
    main()
