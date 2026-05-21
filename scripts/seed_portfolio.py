"""Seed the Alpaca paper account with a diversified-but-tech-heavy demo portfolio.

Allocation (~$50k invested, ~$50k cash remaining out of $100k starting cash):
  Tech (over-weighted, ~60% of invested):
    AAPL   $8,000
    NVDA   $8,000
    MSFT   $8,000
    GOOGL  $6,000
  Finance:    JPM  $7,000
  Energy:     XOM  $7,000
  Healthcare: JNJ  $6,000

Uses notional market orders (fractional shares). Skips symbols already held.
"""
from __future__ import annotations

import sys
import time

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest
from rich.console import Console

from llamafolio.config import load_settings

TARGET_ALLOCATION: dict[str, float] = {
    "AAPL": 8_000,
    "NVDA": 8_000,
    "MSFT": 8_000,
    "GOOGL": 6_000,
    "JPM": 7_000,
    "XOM": 7_000,
    "JNJ": 6_000,
}


def main() -> None:
    console = Console()
    settings = load_settings()
    client = TradingClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
        paper=True,
    )

    clock = client.get_clock()
    if not clock.is_open:
        console.print(
            "[yellow]⚠ Market is closed. Notional market orders are queued and "
            "will fill at next open.[/yellow]"
        )

    held = {p.symbol for p in client.get_all_positions()}
    console.rule("[bold cyan]Seeding portfolio")

    for symbol, dollars in TARGET_ALLOCATION.items():
        if symbol in held:
            console.print(f"  [dim]skip {symbol} (already held)[/dim]")
            continue
        order = MarketOrderRequest(
            symbol=symbol,
            notional=dollars,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
        )
        try:
            resp = client.submit_order(order)
            console.print(f"  [green]✓[/green] {symbol:<6} ${dollars:>6,.0f}  (order {resp.id})")
        except Exception as e:  # noqa: BLE001
            console.print(f"  [red]✗[/red] {symbol:<6} failed: {e}")
        time.sleep(0.2)

    console.rule("[bold cyan]Done")
    console.print("Run [bold]uv run python scripts/check_alpaca.py[/bold] to verify.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
