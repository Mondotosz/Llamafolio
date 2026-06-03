# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Llamafolio** is a multi-agent LLM-powered portfolio advisor for Alpaca paper trading (HEIG-VD Generative AI course, 2026). It uses a router + supervisor architecture with LangGraph for cost-optimized multi-agent orchestration.

## Commands

All commands use `uv` as the package manager.

```bash
# Install dependencies
uv sync

# Launch Streamlit UI (main entry point)
uv run streamlit run app.py

# Verification scripts
uv run python scripts/check_alpaca.py   # Verify Alpaca connection
uv run python scripts/check_mcp.py      # Verify MCP server + list tools
uv run python scripts/check_tools.py    # Verify yfinance + Tavily
uv run python scripts/seed_portfolio.py # Seed demo portfolio (one-off)

# CLI variants (no UI)
uv run python scripts/run_single_agent.py
uv run python scripts/run_multi_agent.py

# Behavioral eval (18 test cases)
uv run python scripts/run_eval.py
uv run python scripts/run_eval.py --filter safety
uv run python scripts/run_eval.py --limit 3

# Build docs (requires Typst CLI)
typst compile --root . docs/rapport.typ docs/rapport.pdf
typst compile --root . docs/slides.typ docs/slides.pdf
typst watch docs/rapport.typ
```

## Environment Setup

Copy `.env.example` to `.env` and populate:

| Variable | Notes |
|---|---|
| `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` | Must be paper trading keys |
| `ALPACA_BASE_URL` | Defaults to `https://paper-api.alpaca.markets` |
| `LLM_PROVIDER` | `gemini`, `groq`, or `ollama` |
| `GOOGLE_API_KEY` | Required if `LLM_PROVIDER=gemini` |
| `GROQ_API_KEY` | Required if `LLM_PROVIDER=groq` |
| `GEMINI_MODEL` | Defaults to `gemini-3.1-flash-lite` |
| `GROQ_MODEL` | Defaults to `openai/gpt-oss-120b` |
| `OLLAMA_MODEL` | Defaults to `qwen3.5:4b` (6.2 GB VRAM, safe for 8 GB GPU); use `qwen3.5:9b` (8.9 GB VRAM) on 16 GB GPU |
| `OLLAMA_BASE_URL` | Defaults to `http://localhost:11434`; set for remote Ollama |
| `TAVILY_API_KEY` | Web search |
| `LANGSMITH_API_KEY` | Optional tracing |

## Architecture

### Two-Layer Orchestration

**Layer 1 — Intent Router** (`src/llamafolio/agents/router.py`): A cheap LLM classifier that routes each user message into one of 7 paths before any expensive agent work begins:

| Path | LLM calls | Handler |
|---|---|---|
| `data` | 0 | Echo pre-fetched portfolio context |
| `analyst` | 1–2 | portfolio_analyst subgraph |
| `research` | 1–2 | research_agent subgraph |
| `risk` | 1–2 | risk_manager subgraph |
| `complex` | 6–12 | Full supervisor chain |
| `executor` | 0–2 | Trade execution (after user confirmation) |
| `decline` | 1 | Polite refusal for out-of-scope |

**Layer 2 — Supervisor Chain** (`src/llamafolio/agents/graph.py`): Used only for `complex` intent. Four specialists: `portfolio_analyst`, `research_agent`, `risk_manager`, `executor`.

### Safety (4-layer defense-in-depth)

1. Router allowlist — only 7 valid intents accepted
2. Structured proposal contract — regex-matched `**Proposed trade**` block (Symbol/Side/Quantity) must precede any execution
3. Programmatic executor guard (`_has_prior_proposal()` in `router.py`) — blocks execution if no prior proposal found in conversation history
4. Paper sandbox — Alpaca MCP filtered to 4 tool buckets; paper key enforced at startup

### Tool Integration

- **Alpaca MCP** (`src/llamafolio/tools/alpaca_mcp.py`): 60+ tools filtered to account/trading/stock-data/news; spawned as stdio subprocess via `uvx alpaca-mcp-server`
- **yfinance** (`src/llamafolio/tools/yfinance_tools.py`): sync, no key, wrapped as `@tool` functions
- **Tavily** (`src/llamafolio/tools/tavily_search.py`): web search for open-ended research

### Key Files

- `src/llamafolio/__init__.py` — public API: `build_graph`, `load_settings`
- `src/llamafolio/config.py` — typed `Settings` dataclass, `.env` loader
- `src/llamafolio/agents/graph.py` — graph construction, LLM factory, specialist agent setup
- `src/llamafolio/agents/router.py` — intent classifier, 7 routing nodes, executor guard
- `src/llamafolio/prompts/` — 7 versioned Markdown prompt files loaded at runtime
- `src/llamafolio/data/portfolio.py` — Alpaca + yfinance sync, context rendering
- `src/llamafolio/ui/chat.py` — streaming message rendering, trade banner, metrics footer

### LLM Configuration

Both providers configured with `temperature=0.1`, `max_retries=5`. Gemini is wrapped with `thinking_budget=0` (required — langgraph-supervisor is incompatible with Gemini's thinking mode).

### Evaluation

`tests/eval_dataset.json` contains 18 behavioral test cases scored on 4 axes: routing, tools, facts, safety. Results written to `tests/eval_results.json` (machine) and `tests/eval_report.md` (human). No CI — eval is run manually.
