# Architecture

## Overview

Llamafolio uses a **supervisor pattern** built on LangGraph: a supervisor
LLM observes the conversation and routes each turn to one of four specialist
ReAct agents. Each specialist owns a focused toolset and a versioned
markdown prompt, then hands control back to the supervisor with its
findings.

```
                       ┌─────────────────┐
   user ─────────────► │   supervisor    │ ◄────── final answer
                       └────────┬────────┘
                                │ transfer_to_*
         ┌──────────────┬───────┴────────┬──────────────┐
         ▼              ▼                ▼              ▼
   ┌──────────┐   ┌──────────┐    ┌──────────┐   ┌──────────┐
   │ analyst  │   │ research │    │   risk   │   │ executor │
   └────┬─────┘   └────┬─────┘    └────┬─────┘   └────┬─────┘
        │              │               │              │
        ▼              ▼               ▼              ▼
  Alpaca MCP     Alpaca MCP       Alpaca MCP    Alpaca MCP
  (account,      (news, market    (stock-bars)  (orders,
   positions)    data)            yfinance      positions)
  yfinance       yfinance         (beta)
                 Tavily
```

## Agents

| Agent | Role | Tools |
| --- | --- | --- |
| **supervisor** | Routes user requests, synthesises the final answer | none (LLM-only) |
| **portfolio_analyst** | Computes composition, sector exposure, concentration | `get_all_positions`, `get_open_position`, `get_account_info`, `get_fundamentals` |
| **research_agent** | Gathers news, fundamentals, market context | `get_news`, `get_stock_snapshot`, `get_stock_latest_quote`, `get_market_movers`, `get_most_active_stocks`, `get_fundamentals`, `get_company_info`, `web_search` |
| **risk_manager** | Evaluates the risk of a proposed change | `get_all_positions`, `get_stock_bars`, `get_fundamentals` |
| **executor** | Places / cancels / closes orders (paper) | `place_stock_order`, `get_orders`, `get_order_by_id`, `cancel_order_by_id`, `cancel_all_orders`, `close_position`, `close_all_positions`, `get_open_position`, `get_account_info` |

## Tool sourcing

- **Alpaca MCP**: the official `alpaca-mcp-server` is launched on demand
  (`uvx alpaca-mcp-server`) over stdio and its tools are imported through
  `langchain-mcp-adapters`. The toolset is filtered to four buckets
  (`account, trading, stock-data, news`) and further pruned by name to keep
  the system prompts small.
- **yfinance** (sync, no key): wraps `yfinance.Ticker(...).info` into two
  LangChain `@tool` functions — `get_fundamentals` and `get_company_info`.
- **Tavily** (`web_search`): used for open-ended research questions that the
  financial-specific tools cannot answer.

## Safety model

1. The executor is **never** invoked on a fresh recommendation. The flow is
   `propose → user explicit confirmation → executor`.
2. The supervisor prompt forbids routing to the executor without an explicit
   "confirm" or "execute" in the user's last message.
3. The executor prompt re-checks the latest user message before placing any
   order and refuses ambiguous instructions.
4. All trades go to a **paper** account (`ALPACA_PAPER_TRADE=True` enforced
   in the MCP server config).

## Why supervisor instead of a single ReAct agent?

A single ReAct agent with all 30+ tools blows past Groq's free-tier
token-per-minute ceiling on Llama 3.3 70B (the schemas alone exceed 12k
tokens). Distributing the tools across four specialists keeps each prompt
small and lets us scale tool count without rate-limit pain.

The repo also ships a single-agent fallback
([src/llamafolio/agents/single_agent.py](../src/llamafolio/agents/single_agent.py))
for ablation / comparison in the project report.

## Observability

LangSmith tracing is opt-in via `LANGSMITH_API_KEY`. EU users should set
`LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com`. Every agent run,
tool call, and prompt is captured and viewable in the LangSmith UI under the
`llamafolio` project.

## Evaluation

A lightweight behavioural eval lives in
[tests/eval_dataset.json](../tests/eval_dataset.json) and is executed by
[scripts/run_eval.py](../scripts/run_eval.py).

Each case scores four dimensions against the multi-agent trail:

| Dimension | What it measures |
| --- | --- |
| **Routing** | Did the expected specialist agents get invoked? |
| **Tools**   | Were the expected MCP / external tools called? |
| **Facts**   | Does the final answer include required substrings (ticker names, "sector", "%", etc.)? |
| **Safety**  | Are forbidden substrings absent (e.g. no `place_stock_order` on an ambiguous "confirm")? |

The 16 cases cover the four specialist roles plus cross-cutting safety
checks (refusing an ambiguous confirmation, refusing to trade an
out-of-scope asset class, etc.). The harness can be filtered to a category
or limited to N cases to keep token usage low while iterating on prompts.

## Known limits

- **Latency**: with 4 specialist agents, a typical multi-turn analysis takes
  10–25 seconds end-to-end (Groq is fast but still 4–8 LLM round-trips).
- **Loop control**: the supervisor caps inter-agent bounces at 5 in its
  prompt; LangGraph itself enforces no global recursion limit by default.
- **No persistence**: the conversation lives in Streamlit session state and
  is lost on tab close. No database, no checkpointer.
- **Eval coverage is small**: 16 cases is enough to catch regressions on
  the main behaviours; a production setup would expand to hundreds and
  include LLM-as-judge for content quality.
