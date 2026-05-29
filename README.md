<p align="center">
  <img src="assets/llamafolio-horizontal-premium.svg" alt="Llamafolio" width="420">
</p>

# Llamafolio

> Multi-agent LLM portfolio advisor for Alpaca paper trading.

Llamafolio analyses an Alpaca paper portfolio, gathers market context,
evaluates risk, and proposes — with explicit user confirmation — trade
adjustments. It is built around a LangGraph **supervisor pattern** sitting
behind an **intent router** that classifies each turn into one of seven
specialised paths, keeping the average cost per turn ~4× lower than a
naïve multi-agent setup.

Final mini-project for the **Generative AI** course at HEIG-VD (2026).

---

## Highlights

- **Router + supervisor architecture** — A 1-call intent classifier
  short-circuits 90 % of requests to a single specialist (or to a zero-LLM
  data path), reserving the full chain for genuinely multi-step requests.
- **Four specialist agents** — `portfolio_analyst`, `research_agent`,
  `risk_manager`, `executor`, each a `create_react_agent` with a focused
  toolkit and a versioned system prompt under
  [`src/llamafolio/prompts/`](src/llamafolio/prompts/).
- **MCP-native tools** — The official `alpaca-mcp-server` is spawned via
  stdio and its 60+ tools are exposed to the agents through
  `langchain-mcp-adapters`. Tavily and yfinance complete the toolbox.
- **Defense-in-depth safety** — Router allowlist + structured proposal
  contract + **programmatic guard** on the executor (no LLM call without a
  matching prior proposal) + paper-only sandbox. The eval harness
  discovered and verified the fix for a forged-confirmation bypass.
- **Dual provider** — Gemini 3.1 Flash Lite (default) or Groq gpt-oss-120b,
  switchable via `LLM_PROVIDER` in `.env`. No code change required.
- **Pre-fetch portfolio context** — A host-side Alpaca read is injected
  into every turn, saving 8–10 MCP round-trips per analyst question.
- **Behavioural eval harness** — 18 cases across 7 router paths, scored on
  routing, tools, facts, and safety. Latest run: **1.00 across all 4 axes**
  on 16/18 cases (2 rate-limited).
- **Streaming UI** — Streamlit timeline with per-agent bubbles, a strict
  `Confirm / Refuse` banner triggered only by structured proposals, and a
  per-turn metrics footer (specialists / tool calls / round-trips / time).

---

## Architecture

```
   ┌──────────────────────────────────────────────────────────────────┐
   │                  Streamlit UI (host)                              │
   │  ┌────────────────────┐  pre-fetch Alpaca  ┌─────────────────┐    │
   │  │ user question      │ ─────────────────► │ <portfolio_ctx> │    │
   │  └─────────┬──────────┘                    └────────┬────────┘    │
   └────────────┼──────────────────────────────────────────┼───────────┘
                ▼                                          ▼
            ┌──────────────────────────────────────────────┐
            │            intent router (1 LLM call)         │
            └──┬────────────┬────────────┬────────────┬─────┘
               │            │            │            │
        ┌──────┴──┐  ┌──────┴──┐  ┌──────┴──┐  ┌──────┴──────┐
        ▼         ▼  ▼         ▼  ▼         ▼  ▼             ▼
       data   analyst  research  risk  executor*  complex (supervisor chain)
       0 LLM    2 LLM   2 LLM    2 LLM   2 LLM      6–12 LLM round-trips

   * executor guarded by `_has_prior_proposal` — refuses deterministically
     without a matching **Proposed trade** block in the AI history.
```

| Intent path | Typical question | LLM calls | Latency |
| --- | --- | ---:| ---:|
| `data` | *What's in my portfolio?* | 1 (router) | ~1 s |
| `analyst` | *Analyse my sector exposure.* | 2 | ~5 s |
| `research` | *News on NVDA today?* | 2 | ~6 s |
| `risk` | *What if I sold 50 % of NVDA?* | 2 | ~5 s |
| `complex` | *Suggest one trim with research and risk check.* | 6–12 | ~30 s |
| `executor` | *confirm sell NVDA $1800* | 0–2 | ~1–4 s |
| `decline` | *What's the weather today?* | 1 | ~1 s |

See [docs/architecture.md](docs/architecture.md) for the full breakdown,
and [docs/rapport.pdf](docs/rapport.pdf) for the complete written report.

---

## Stack

| Layer | Choice | Why |
| --- | --- | --- |
| LLM (default) | **Gemini 3.1 Flash Lite** | 250 k TPM, 15 RPM free, native parallel tool calling, multilingual |
| LLM (failover) | Groq **gpt-oss-120b** | ~500 t/s, quality on par, switchable via `.env` |
| Orchestration | LangGraph + `langgraph-supervisor` | Streaming, explicit state, supervisor pattern |
| Trading | Alpaca paper trading | Realistic execution semantics, free, no KYC |
| MCP tools | `alpaca-mcp-server` (FastMCP) | Official, 60+ tools via Model Context Protocol |
| Web search | Tavily | LLM-friendly search API, free tier |
| Fundamentals | yfinance | No key required, complements Alpaca |
| UI | Streamlit + Plotly | Streaming-native, demo-friendly |
| Tracing | LangSmith (EU endpoint) | Multi-agent traces, prompt versioning, GDPR |
| Packaging | `uv` | Deterministic lockfile, 10× faster than pip |
| Reporting | Typst + Touying | PDF report and slides versioned in-repo |

---

## Quickstart

Requires Python ≥ 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
# 1. Clone
git clone <repo-url> && cd IAG-AI-Trademaxxing

# 2. Configure secrets
cp .env.example .env
#   then edit .env with your Alpaca paper, Gemini (or Groq),
#   Tavily, and (optionally) LangSmith keys.

# 3. Install
uv sync

# 4. Verify the connection to Alpaca
uv run python scripts/check_alpaca.py

# 5. Seed a demo portfolio (one-off, paper account)
uv run python scripts/seed_portfolio.py

# 6. Launch the app
uv run streamlit run app.py
```

The app is served at <http://localhost:8501>.

### Required API keys (all free tiers)

| Service | Used for | Sign up |
| --- | --- | --- |
| [Alpaca](https://alpaca.markets/) | Paper trading, market data, news | Free |
| [Google AI Studio](https://aistudio.google.com/apikey) | Gemini 3.1 Flash Lite (default LLM) | Free, 15 RPM / 500 RPD |
| [Groq](https://console.groq.com/) | gpt-oss-120b (alternate LLM) | Free |
| [Tavily](https://tavily.com/) | Web search | Free, 1000 req/mo |
| [LangSmith](https://smith.langchain.com/) | Tracing (optional) | Free, 5000 traces/mo |

Switch LLM provider with `LLM_PROVIDER=gemini` (default) or
`LLM_PROVIDER=groq` in `.env`. No code change needed.

---

## Project structure

```
.
├── app.py                            # Streamlit entry point (9-line shim)
├── pyproject.toml                    # Project + deps (uv lock)
├── .env.example                      # Template for required secrets
├── .streamlit/config.toml            # Light theme
├── assets/                           # Brand kit (logos, avatars, favicons)
├── docs/
│   ├── architecture.md               # Technical overview
│   ├── rapport.typ / rapport.pdf     # Full written report (FR, Typst)
│   └── slides.typ  / slides.pdf      # Presentation deck (FR, Touying)
├── scripts/                          # CLI utilities
│   ├── check_alpaca.py               #   verify Alpaca connection
│   ├── check_mcp.py                  #   verify MCP server + list tools
│   ├── check_tools.py                #   verify yfinance + Tavily
│   ├── seed_portfolio.py             #   seed a tech-heavy demo portfolio
│   ├── run_single_agent.py           #   CLI baseline (no UI)
│   ├── run_multi_agent.py            #   CLI multi-agent (no UI)
│   └── run_eval.py                   #   eval harness, writes tests/eval_*
├── src/llamafolio/                   # Package source (src/ layout)
│   ├── __init__.py                   #   public API: build_graph, load_settings
│   ├── config.py                     #   typed .env loader
│   ├── prompts/                      #   versioned agent prompts (Markdown)
│   ├── agents/
│   │   ├── graph.py                  #   build_graph entry point
│   │   ├── router.py                 #   intent router + executor guard
│   │   └── single_agent.py           #   fallback baseline
│   ├── tools/                        #   LangChain tools
│   │   ├── alpaca_mcp.py             #   Alpaca MCP adapter
│   │   ├── tavily_search.py          #   web search
│   │   └── yfinance_tools.py         #   fundamentals + company info
│   ├── data/                         #   pure data access (no UI)
│   │   └── portfolio.py              #   Alpaca + yfinance sync helpers
│   └── ui/                           #   Streamlit UI (one module per surface)
│       ├── main.py                   #   composes the page
│       ├── styles.py                 #   CSS
│       ├── assets.py                 #   static paths + base64 helper
│       ├── messages.py               #   LangChain message helpers
│       ├── charts.py                 #   Plotly sparkline + donut
│       ├── header.py                 #   top brand band
│       ├── sidebar.py                #   portfolio dashboard
│       ├── empty_state.py            #   welcome + agent grid + suggestions
│       ├── trade_detector.py         #   parses structured proposals
│       └── chat.py                   #   streaming turn + banner + metrics
└── tests/
    ├── eval_dataset.json             # 18 behavioural eval cases (v2.0)
    ├── eval_results.json             # latest run, machine-readable
    ├── eval_report.md                # latest run, human-readable
    └── eval_*.before_patch.*         # archived pre-patch baseline
```

The `src/` layout keeps every importable artefact under
`src/llamafolio/`; the root only carries the Streamlit entry point and
top-level config. `app.py` is a 9-line shim; the real work lives in
`llamafolio.ui.main`.

---

## Eval harness

The eval harness drives the full graph through `tests/eval_dataset.json`
(18 cases across 7 router paths) and scores each case on four axes:

| Axis | Measure |
| --- | --- |
| **Routing** | Share of expected agents observed in the trace |
| **Tools** | Share of expected tools observed (only fresh fetches; pre-fetched context covers positions/sectors) |
| **Facts** | Substring presence of expected facts in the assistant content |
| **Safety** | Absence of forbidden substrings (e.g. `place_stock_order` after an ambiguous "confirm") |

Run the full eval:

```bash
uv run python scripts/run_eval.py
```

Or target a subset:

```bash
uv run python scripts/run_eval.py --cases router-data-portfolio-display,safety-refuse-ambiguous-confirm
```

Two artefacts are produced on every run: `tests/eval_results.json` (machine)
and `tests/eval_report.md` (human, committable). The report breaks down
results per category and per case, with observed agents and tools.

### Latest results (Gemini 3.1 Flash Lite, post-patch)

| Category | n | Routing | Tools | Facts | Safety | avg s |
| --- | ---:| ---:| ---:| ---:| ---:| ---:|
| data | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 6.1 |
| analyst | 3 | 1.00 | 1.00 | 1.00 | 1.00 | 5.3 |
| research | 5 | 1.00 | 1.00 | 1.00 | 1.00 | 5.7 |
| complex | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 40.3 |
| safety | 5 | 1.00 | 1.00 | 1.00 | 1.00 | 7.8 |
| multilingual | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 21.9 |

**1.00 on all four axes across 16/18 cases.** The remaining 2 cases were
rate-limited mid-run by Gemini's free tier; the paths they test are
covered by other cases in the same category.

---

## Safety

Llamafolio enforces trade-safety in four cumulative layers:

1. **Router allowlist** — every turn is classified into one of seven
   intents; out-of-scope requests are routed to `decline`.
2. **Structured proposal contract** — the UI's `Confirm / Refuse` banner
   only appears when a strict `**Proposed trade**` block (with `Symbol:`,
   `Side:`, `Quantity:` lines) is detected in the assistant response.
3. **Programmatic guard on the executor** — `_has_prior_proposal()` scans
   `state["messages"]` for an `AIMessage` containing a structured proposal
   **before** invoking the executor LLM. Without one, the executor returns
   a deterministic refusal — no LLM call, no tool call.
4. **Paper sandbox** — the MCP toolset is filtered to
   `account,trading,stock-data,news`, and the Alpaca key must be a paper
   key (verified at startup).

The programmatic guard was added after the eval harness discovered that
the executor's system prompt alone was insufficient: the model was
hallucinating implicit proposals from confirmation text like
`"confirm sell NVDA $1500"`. Full incident write-up in
[docs/rapport.pdf § 6.6](docs/rapport.pdf).

---

## Scripts

| Script | Purpose |
| --- | --- |
| `scripts/check_alpaca.py` | Verify Alpaca connection — print account + positions |
| `scripts/check_mcp.py` | Verify the Alpaca MCP server — list exposed tools |
| `scripts/check_tools.py` | Verify yfinance + Tavily tools |
| `scripts/seed_portfolio.py` | Seed a tech-heavy demo portfolio |
| `scripts/run_single_agent.py` | Run the single-agent baseline (CLI, no UI) |
| `scripts/run_multi_agent.py` | Run the multi-agent supervisor graph (CLI, no UI) |
| `scripts/run_eval.py` | Score the graph against `tests/eval_dataset.json` |

---

## Building the report and slides

The report (`docs/rapport.typ`) and slides (`docs/slides.typ`) are
authored in [Typst](https://typst.app/). Install the CLI once
(`brew install typst` on macOS, `cargo install --locked typst-cli` on
Linux, or your distro's package), then from the repository root:

```bash
typst compile --root . docs/rapport.typ docs/rapport.pdf
typst compile --root . docs/slides.typ  docs/slides.pdf
```

Use `typst watch <path>` for hot reload while iterating. The slides
depend on the [`touying`](https://typst.app/universe/package/touying)
package; Typst downloads it automatically from Typst Universe on the
first compile.

---

## Roadmap

- [x] Behavioural eval harness with auto-scoring on routing / tools / facts / safety
- [x] Intent router in front of the supervisor for 4× cost reduction
- [x] Dual provider (Gemini / Groq) switchable via `.env`
- [x] Pre-fetch portfolio context to eliminate 8–10 MCP round-trips per turn
- [x] Programmatic safety guard on the executor
- [x] Structured proposal contract + `Confirm / Refuse` banner
- [ ] LLM-as-judge for content quality on top of the substring-match eval
- [ ] Adversarial eval pack (prompt injection, forged proposals, multilingual confirmations)
- [ ] GitHub Actions CI: lint, type-check, and run the eval on every PR
- [ ] LangGraph checkpointer + SQLite/Postgres for cross-session memory
- [ ] Explicit prompt caching on the five agent system prompts
- [ ] Streamlit Cloud deployment for a public demo
- [ ] Minimal backtest of the agent's recommendations on historical data

---

## Authors

Victor & Kenan — HEIG-VD, Generative AI course, 2026.

Project supervised by Nastaran Fatemi, Andrei Popescu-Belis, Shabnam Ataee,
and Christopher Meier.

---

## License

[GNU GPLv3](LICENSE).
