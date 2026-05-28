"""LangChain message helpers used by the streaming chat UI.

Two small concerns live here:

- `content_text(msg)` — robust text extraction that handles both the
  classic `str` content shape and the list-of-parts shape that
  Gemini 3.x returns (e.g. `[{'type': 'text', 'text': '...'}]`).
- `step_label(msg)` — maps an `AIMessage` with `tool_calls` to a
  `(kind, body_html)` row for the live agent timeline expander
  (route / done / tool).

These are presentation-only utilities: they never mutate state and have
no Streamlit side-effects.
"""
from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage

# Substrings that mark the synthetic "handoff" AIMessages emitted by
# langgraph-supervisor (and our router) when a specialist hands the
# conversation back. The chat UI hides these so they don't pollute the
# visible bubbles next to the real agent output.
HANDOFF_NOISE: tuple[str, ...] = (
    "transferred back",
    "transferring back",
    "handing back",
)


def content_text(m: Any) -> str:
    """Return the text content of a LangChain message regardless of shape."""
    c = getattr(m, "content", "") or ""
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts: list[str] = []
        for chunk in c:
            if isinstance(chunk, str):
                parts.append(chunk)
            elif isinstance(chunk, dict):
                text = chunk.get("text") or chunk.get("content") or ""
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)
    return str(c)


def step_label(m: Any) -> tuple[str, str] | None:
    """Return `(kind, body_html)` for a routing / tool-call AIMessage.

    The body is small HTML (a `<span>`) ready to drop into the live
    timeline expander. Returns None for messages that should not appear
    in the timeline at all (content-only AIMessages, ToolMessages,
    HumanMessages, etc.).
    """
    name = getattr(m, "name", None) or "supervisor"
    if isinstance(m, AIMessage) and m.tool_calls:
        for tc in m.tool_calls:
            t = tc["name"]
            if t.startswith("transfer_to_"):
                target = t.removeprefix("transfer_to_")
                return ("route", f"<span class='lf-step-name'>{target}</span>")
            if t.startswith("transfer_back"):
                return ("done", f"<span class='lf-step-name'>{name}</span>")
            return ("tool", f"<span class='lf-step-name'>{name} &middot; {t}</span>")
    return None
