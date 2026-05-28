<p align="center">
  <img src="assets/llamafolio-horizontal-premium.svg" alt="Llamafolio" width="420">
</p>

# Llamafolio

> Multi-agent LLM portfolio advisor for Alpaca paper trading.

Llamafolio is a proof-of-concept agent system that analyses an Alpaca paper
portfolio, gathers market context, evaluates risk, and proposes — with explicit
user confirmation — trade adjustments. It is built around a LangGraph
**supervisor pattern** orchestrating four specialist agents, with tools wired
through the **Model Context Protocol (MCP)**.

Final mini-project for the **Generative AI** course at HEIG-VD (2026).

---

## Highlights

- **Multi-agent**: a supervisor routes user requests to four specialists
  (portfolio analyst, research, risk, executor) and synthesises a final
  answer.
- **MCP-native tools**: the official Alpaca MCP server is spawned via stdio
  and its tools (account, trading, market data, news) are exposed to the
  agents through `langchain-mcp-adapters`.
- **Versioned prompts**: every agent's system prompt lives as a markdown file
  in `src/llamafolio/prompts/`, tracked in git.
- **Safety**: trades are *never* executed without an explicit confirmation in
  the user message; the executor agent refuses ambiguous instructions.
- **Streamlit UI**: light, data-forward interface with a portfolio dashboard,
  chat, and a live timeline of the agents' routing decisions.
- **Free stack**: Groq (Llama 3.3 70B), Alpaca paper trading, Tavily,
  yfinance, LangSmith — all on free tiers.

---

## Architecture

```
                       ┌─────────────────┐
   user ─────────────► │   supervisor    │ ────── final answer
                       └────────┬────────┘
                                │ routes to one of:
         ┌──────────────┬───────┴────────┬──────────────┐
         ▼              ▼                ▼              ▼
   ┌──────────┐   ┌──────────┐    ┌──────────┐   ┌──────────┐
   │ analyst  │   │ research │    │   risk   │   │ executor │
   └──────────┘   └──────────┘    └──────────┘   └──────────┘
   positions      news/web        beta/vol       place_order
   sector exp.    fundamentals    exposure       cancel/close
```

Each specialist is a `create_react_agent` with a focused subset of tools.
Tool distribution keeps each agent's system prompt small enough to fit under
Groq's free-tier rate limit.

See [docs/architecture.md](docs/architecture.md) for the full breakdown.

---

## Stack

| Layer | Choice | Why |
| --- | --- | --- |
| LLM | Groq · Llama 3.3 70B | Free, fast, decent tool calling |
| Orchestration | LangGraph + `langgraph-supervisor` | Multi-agent supervisor pattern |
| Trading | Alpaca paper trading | Free, realistic execution semantics |
| MCP tools | `alpaca-mcp-server` (FastMCP) | Official, 30+ tools out of the box |
| Web search | Tavily | LLM-friendly search API, free tier |
| Fundamentals | yfinance | No key required, complements Alpaca |
| UI | Streamlit + Plotly | Quick to build, demo-friendly |
| Tracing | LangSmith (EU endpoint) | Debug multi-agent runs |
| Tooling | `uv`, `ruff` | Modern Python tooling |

---

## Quickstart

Requires Python ≥ 3.11 and [uv](https://docs.astral.sh/uv/).

```bash
# 1. Clone
git clone <repo-url> && cd IAG-AI-Trademaxxing

# 2. Configure secrets
cp .env.example .env
#   then edit .env with your Alpaca paper, Groq, Tavily,
#   and (optionally) LangSmith keys.

# 3. Install
uv sync

# 4. Verify the connection to Alpaca
uv run python scripts/check_alpaca.py

# 5. Seed a demo portfolio (one-off, paper account)
uv run python scripts/seed_portfolio.py

# 6. Launch the app
uv run streamlit run app.py
```

The app is then served at <http://localhost:8501>.

### Required API keys (all free tiers)

| Service | Used for | Sign up |
| --- | --- | --- |
| [Alpaca](https://alpaca.markets/) | Paper trading, market data, news | Free |
| [Groq](https://console.groq.com/) | LLM inference (Llama 3.3 70B) | Free |
| [Tavily](https://tavily.com/) | Web search | Free, 1000 req/mo |
| [LangSmith](https://smith.langchain.com/) | Tracing (optional) | Free, 5000 traces/mo |

---

## Project structure

```
.
├── app.py                            # Streamlit entry point (thin shim)
├── pyproject.toml                    # Project + deps (uv)
├── .env.example                      # Template for required secrets
├── .streamlit/
│   └── config.toml                   # Light theme
├── assets/                           # Brand kit (logo lockups, icons, avatars)
├── docs/
│   ├── architecture.md               # Technical overview
│   ├── rapport.typ                   # 2-3 page report (FR, Typst)
│   └── slides.typ                    # 10-min slide deck (FR, Typst + Touying)
├── scripts/                          # CLI utilities (verb-prefixed)
│   ├── check_alpaca.py
│   ├── check_mcp.py
│   ├── check_tools.py
│   ├── seed_portfolio.py
│   ├── run_single_agent.py
│   ├── run_multi_agent.py
│   └── run_eval.py
├── src/llamafolio/                   # Package source (src/ layout)
│   ├── config.py                     # Typed .env loader
│   ├── prompts/                      # Versioned agent prompts (Markdown)
│   ├── agents/                       # Agentic core
│   │   ├── graph.py                  #   build_graph entry point
│   │   ├── router.py                 #   intent router (pre-classifier)
│   │   └── single_agent.py           #   fallback baseline
│   ├── tools/                        # LangChain tools
│   │   ├── alpaca_mcp.py             #   Alpaca MCP server adapter
│   │   ├── tavily_search.py          #   web search
│   │   └── yfinance_tools.py         #   fundamentals + company info
│   ├── data/                         # Pure data access (no UI, no LangChain)
│   │   └── portfolio.py              #   Alpaca + yfinance sync helpers
│   └── ui/                           # Streamlit UI (one module per surface)
│       ├── main.py                   #   composes the page
│       ├── styles.py                 #   CSS
│       ├── assets.py                 #   static paths + base64 helper
│       ├── messages.py               #   LangChain message helpers
│       ├── charts.py                 #   Plotly sparkline + donut
│       ├── header.py                 #   top brand band
│       ├── sidebar.py                #   portfolio dashboard
│       ├── empty_state.py            #   welcome + agent grid + chips
│       ├── trade_detector.py         #   parses structured proposals
│       └── chat.py                   #   streaming turn + banner + metrics
└── tests/
    └── eval_dataset.json             # Behavioural eval cases
```

The `src/` layout keeps every importable artefact under
`src/llamafolio/`; the root only carries the Streamlit entry point and
top-level config.

---

## Scripts

| Script | Purpose |
| --- | --- |
| `scripts/check_alpaca.py` | Verify Alpaca connection — print account + positions |
| `scripts/check_mcp.py` | Verify the Alpaca MCP server — list exposed tools |
| `scripts/check_tools.py` | Verify yfinance + Tavily tools |
| `scripts/seed_portfolio.py` | Seed a demo portfolio (tech-heavy, ~$50k) |
| `scripts/run_single_agent.py` | Run the single-agent fallback (CLI, no UI) |
| `scripts/run_multi_agent.py` | Run the multi-agent supervisor graph (CLI, no UI) |
| `scripts/run_eval.py` | Score the multi-agent on `tests/eval_dataset.json` |

---

## Building the report and slides

The report (`docs/rapport.typ`) and slides (`docs/slides.typ`) are
authored in [Typst](https://typst.app/). Install the CLI once
(`brew install typst` on macOS, `cargo install --locked typst-cli` on
Linux, or your distro's package), then from the repository root:

```bash
typst compile docs/rapport.typ docs/rapport.pdf
typst compile docs/slides.typ docs/slides.pdf
```

Use `typst watch <path>` for hot reload while iterating. The slides
depend on the [`touying`](https://typst.app/universe/package/touying)
package; Typst downloads it automatically from Typst Universe on the
first compile.

---

## Roadmap

- [x] Behavioural eval harness with auto-scoring on routing / tools / facts / safety
- [ ] LLM-as-judge for content quality on top of the behavioural eval
- [ ] Minimal backtest of the agent's recommendations on historical data
- [ ] Action buttons in the UI for "confirm / refuse" proposed trades
- [ ] Restrict MCP toolset further to reduce TPM pressure
- [ ] Streamlit Cloud deployment for a public demo

---

## Authors

Victor & Kenan — HEIG-VD, Generative AI course, 2026.

Project supervised by Nastaran Fatemi, Andrei Popescu-Belis, Shabnam Ataee,
and Christopher Meier.

---

## License

[GNU GPLv3](LICENSE).
