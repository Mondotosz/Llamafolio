"""Detect structured trade proposals in agent output.

The supervisor's contract for proposing a trade is:

    **Proposed trade**
    Symbol: NVDA
    Side: SELL
    Quantity: $1,500 (or '25%', or '10 shares')
    Rationale: <one sentence>

When the UI sees a message matching this contract, it surfaces a
Confirm / Refuse button pair. The detector is strict on purpose: a
false positive here lets the user click Confirm and place a real
(paper) order they did not mean to send.

A "proposal header" (one of the recognised phrases) AND a
`Symbol: X / Side: Y / Quantity: Z` label block are both required.
Casual mentions of "trim" or "%" in narrative prose are ignored.
"""
from __future__ import annotations

import re

_PROPOSED_TRADE_HEADERS: tuple[str, ...] = (
    "proposed trade",
    "proposed action",
    "recommended trade",
)

_LABEL_PATTERN = re.compile(
    r"symbol[:\s]+([A-Z]{2,5})\b"
    r".{0,200}?"
    r"\b(buy|sell|trim|reduce)\b"
    r".{0,200}?"
    r"(?:quantity|qty|amount|size)[:\s]+([^\n]+?)(?:\n|$)",
    re.IGNORECASE | re.DOTALL,
)


def detect_proposed_trade(text: str) -> dict | None:
    """Return `{"symbol", "side", "qty"}` when `text` contains a proposal
    block, else `None`. `side` is normalised to `'buy'` or `'sell'`."""
    if not text:
        return None
    low = text.lower()
    if not any(h in low for h in _PROPOSED_TRADE_HEADERS):
        return None
    m = _LABEL_PATTERN.search(text)
    if not m:
        return None

    symbol = m.group(1).upper()
    side = m.group(2).lower()
    qty_raw = m.group(3).strip()

    if side in ("trim", "reduce"):
        side = "sell"

    # Strip trailing "(...)" parenthetical and any dangling punctuation.
    qty = qty_raw.split("(")[0].strip().rstrip(".,")
    if not qty:
        return None
    return {"symbol": symbol, "side": side, "qty": qty}
