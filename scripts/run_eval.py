"""Lightweight behavioural evaluation harness for the multi-agent graph.

For each case in tests/eval_dataset.json:
  1. invoke the multi-agent graph with the case's question
  2. inspect the message trail to extract which agents were routed to and
     which tools were called
  3. score against the case's expectations: routing, tooling, facts, safety
  4. print a per-case table and a summary

Use the --limit / --filter options to keep token usage low. Results are
also written to tests/eval_results.json for the report.

Example:
    uv run python scripts/run_eval.py --limit 3
    uv run python scripts/run_eval.py --filter safety
"""
from __future__ import annotations

import argparse
import asyncio
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from rich.console import Console
from rich.table import Table

from llamafolio.agents.graph import build_graph
from llamafolio.config import load_settings
from llamafolio.data import (
    load_account,
    load_equity_history,
    load_positions,
    render_portfolio_context,
)

DATASET_PATH = Path(__file__).parent.parent / "tests" / "eval_dataset.json"
RESULTS_PATH = Path(__file__).parent.parent / "tests" / "eval_results.json"
REPORT_PATH = Path(__file__).parent.parent / "tests" / "eval_report.md"


@dataclass
class CaseScore:
    case_id: str
    category: str
    routing: float
    tools: float
    facts: float
    safety: float
    overall: float
    elapsed_s: float
    error: str | None = None
    observed_agents: list[str] = field(default_factory=list)
    observed_tools: list[str] = field(default_factory=list)


def _safe_pct(num: int, denom: int) -> float:
    return 1.0 if denom == 0 else num / denom


def _content_text(m) -> str:
    """Extract text from a LangChain message, handling both the classic
    `str` content shape and the list-of-parts shape returned by Gemini
    3.x (e.g. `[{'type': 'text', 'text': '...'}]`)."""
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


def _extract_trail(messages: list) -> tuple[list[str], list[str], str]:
    """Return (observed_agents, observed_tools, concatenated_content)."""
    agents: list[str] = []
    tools: list[str] = []
    content_chunks: list[str] = []
    for m in messages:
        if isinstance(m, AIMessage):
            name = getattr(m, "name", None)
            if name and name != "supervisor" and name not in agents:
                agents.append(name)
            for tc in (m.tool_calls or []):
                t = tc["name"]
                if t.startswith("transfer_to_") or t.startswith("transfer_back"):
                    continue
                if t not in tools:
                    tools.append(t)
            text = _content_text(m)
            if text and not m.tool_calls:
                content_chunks.append(text)
        elif isinstance(m, ToolMessage):
            tname = getattr(m, "name", None)
            if tname and tname not in tools:
                tools.append(tname)
            # ToolMessage content may also be a list-of-parts on Gemini.
            text = _content_text(m)
            if text:
                content_chunks.append(text)
    return agents, tools, "\n".join(content_chunks)


def _score_case(case: dict, messages: list) -> dict:
    observed_agents, observed_tools, content = _extract_trail(messages)
    content_low = content.lower()

    exp_agents = set(case["expected_agents"])
    routing = _safe_pct(
        sum(1 for a in exp_agents if a in observed_agents), len(exp_agents)
    )

    exp_tools = set(case["expected_tools"])
    tools_score = _safe_pct(
        sum(1 for t in exp_tools if t in observed_tools), len(exp_tools)
    )

    exp_facts = case["expected_facts"]
    facts_score = _safe_pct(
        sum(1 for f in exp_facts if f.lower() in content_low), len(exp_facts)
    )

    forbidden = case["forbidden_substrings"]
    safety = 0.0 if any(f.lower() in content_low for f in forbidden) else 1.0

    overall = (routing + tools_score + facts_score + safety) / 4
    return {
        "observed_agents": observed_agents,
        "observed_tools": observed_tools,
        "routing": routing,
        "tools": tools_score,
        "facts": facts_score,
        "safety": safety,
        "overall": overall,
    }


def _wrap_with_portfolio_context(question: str) -> str:
    """Reproduce the UI's pre-fetch + injection so the eval exercises the
    same prompt shape that production turns receive. Falls back to the raw
    question if Alpaca cannot be reached."""
    try:
        settings = load_settings()
        ctx = render_portfolio_context(
            load_account(settings),
            load_positions(settings),
            load_equity_history(settings, period="1D", timeframe="1Min"),
        )
        return f"{ctx}\n\nUser question: {question}"
    except Exception:  # noqa: BLE001
        return question


async def _run_case(graph, case: dict) -> CaseScore:
    start = time.perf_counter()
    try:
        wrapped = _wrap_with_portfolio_context(case["question"])
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=wrapped)]}
        )
        elapsed = time.perf_counter() - start
        s = _score_case(case, result["messages"])
        return CaseScore(
            case_id=case["id"],
            category=case["category"],
            routing=s["routing"],
            tools=s["tools"],
            facts=s["facts"],
            safety=s["safety"],
            overall=s["overall"],
            elapsed_s=elapsed,
            observed_agents=s["observed_agents"],
            observed_tools=s["observed_tools"],
        )
    except Exception as e:  # noqa: BLE001
        return CaseScore(
            case_id=case["id"],
            category=case["category"],
            routing=0.0, tools=0.0, facts=0.0, safety=0.0, overall=0.0,
            elapsed_s=time.perf_counter() - start,
            error=str(e)[:300],
        )


async def main_async(
    limit: int | None,
    category_filter: str | None,
    case_ids: list[str] | None,
) -> None:
    console = Console()
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    cases = dataset["cases"]
    if case_ids:
        wanted = set(case_ids)
        cases = [c for c in cases if c["id"] in wanted]
        missing = wanted - {c["id"] for c in cases}
        if missing:
            console.print(f"[yellow]unknown case ids: {', '.join(sorted(missing))}[/yellow]")
    if category_filter:
        cases = [c for c in cases if category_filter in c["category"]]
    if limit:
        cases = cases[:limit]

    console.rule(f"[bold cyan]Llamafolio eval — {len(cases)} case(s)")
    graph = await build_graph()

    results: list[CaseScore] = []
    for i, case in enumerate(cases, 1):
        console.print(f"[dim]({i}/{len(cases)})[/dim] [bold]{case['id']}[/bold] [{case['category']}]")
        score = await _run_case(graph, case)
        results.append(score)
        if score.error:
            console.print(f"  [red]error:[/red] {score.error}")

    # Summary table
    table = Table(show_header=True, header_style="bold magenta")
    for col in ("Case", "Cat", "Route", "Tools", "Facts", "Safety", "Overall", "s"):
        table.add_column(col)
    for r in results:
        table.add_row(
            r.case_id,
            r.category,
            f"{r.routing:.2f}",
            f"{r.tools:.2f}",
            f"{r.facts:.2f}",
            f"{r.safety:.2f}",
            f"{r.overall:.2f}",
            f"{r.elapsed_s:.1f}",
        )
    console.rule("[bold cyan]Results")
    console.print(table)

    n = max(len(results), 1)
    avg = {
        "routing": sum(r.routing for r in results) / n,
        "tools":   sum(r.tools   for r in results) / n,
        "facts":   sum(r.facts   for r in results) / n,
        "safety":  sum(r.safety  for r in results) / n,
        "overall": sum(r.overall for r in results) / n,
        "elapsed_avg_s": sum(r.elapsed_s for r in results) / n,
        "errors": sum(1 for r in results if r.error),
        "n": n,
    }
    console.rule("[bold cyan]Summary")
    for k, v in avg.items():
        console.print(f"  {k:<14} {v:.2f}" if isinstance(v, float) else f"  {k:<14} {v}")

    # Per-category breakdown — the headline aggregation for the report.
    by_cat: dict[str, list[CaseScore]] = {}
    for r in results:
        by_cat.setdefault(r.category, []).append(r)

    cat_table = Table(show_header=True, header_style="bold magenta")
    for col in ("Category", "n", "Route", "Tools", "Facts", "Safety", "Overall", "avg s"):
        cat_table.add_column(col)
    cat_rows: list[dict] = []
    for category, rows in sorted(by_cat.items()):
        k = len(rows)
        row = {
            "category": category,
            "n": k,
            "routing": sum(r.routing for r in rows) / k,
            "tools":   sum(r.tools   for r in rows) / k,
            "facts":   sum(r.facts   for r in rows) / k,
            "safety":  sum(r.safety  for r in rows) / k,
            "overall": sum(r.overall for r in rows) / k,
            "elapsed_avg_s": sum(r.elapsed_s for r in rows) / k,
        }
        cat_rows.append(row)
        cat_table.add_row(
            category, str(k),
            f"{row['routing']:.2f}", f"{row['tools']:.2f}",
            f"{row['facts']:.2f}", f"{row['safety']:.2f}",
            f"{row['overall']:.2f}", f"{row['elapsed_avg_s']:.1f}",
        )
    console.rule("[bold cyan]Per-category breakdown")
    console.print(cat_table)

    # Persist a JSON snapshot AND a Markdown report ready to paste into
    # the project report / slides.
    RESULTS_PATH.write_text(
        json.dumps(
            {
                "summary": avg,
                "by_category": cat_rows,
                "cases": [asdict(r) for r in results],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    REPORT_PATH.write_text(_render_markdown_report(avg, cat_rows, results), encoding="utf-8")
    console.print(f"\n[dim]Wrote {RESULTS_PATH.relative_to(Path.cwd())}[/dim]")
    console.print(f"[dim]Wrote {REPORT_PATH.relative_to(Path.cwd())}[/dim]")


def _render_markdown_report(
    summary: dict, by_cat: list[dict], cases: list[CaseScore]
) -> str:
    """Render a Markdown report ready to paste in the project deliverable."""
    lines: list[str] = []
    lines.append("# Llamafolio — eval report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Cases: **{summary['n']}**")
    lines.append(f"- Errors: **{summary['errors']}**")
    lines.append(f"- Average latency: **{summary['elapsed_avg_s']:.1f}s**")
    lines.append("")
    lines.append("| Axis | Score |")
    lines.append("|---|---|")
    for axis in ("routing", "tools", "facts", "safety", "overall"):
        lines.append(f"| {axis.title()} | **{summary[axis]:.2f}** |")
    lines.append("")
    lines.append("## By category")
    lines.append("")
    lines.append("| Category | n | Routing | Tools | Facts | Safety | Overall | avg s |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for r in by_cat:
        lines.append(
            f"| {r['category']} | {r['n']} | "
            f"{r['routing']:.2f} | {r['tools']:.2f} | "
            f"{r['facts']:.2f} | {r['safety']:.2f} | "
            f"{r['overall']:.2f} | {r['elapsed_avg_s']:.1f} |"
        )
    lines.append("")
    lines.append("## Per-case detail")
    lines.append("")
    lines.append("| Case | Cat | Route | Tools | Facts | Safety | Overall | s | Observed agents | Observed tools |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---|---|")
    for c in cases:
        ag = ", ".join(c.observed_agents) or "—"
        to = ", ".join(c.observed_tools) or "—"
        err = " ⚠" if c.error else ""
        lines.append(
            f"| {c.case_id}{err} | {c.category} | "
            f"{c.routing:.2f} | {c.tools:.2f} | "
            f"{c.facts:.2f} | {c.safety:.2f} | "
            f"{c.overall:.2f} | {c.elapsed_s:.1f} | "
            f"{ag} | {to} |"
        )
    errors = [c for c in cases if c.error]
    if errors:
        lines.append("")
        lines.append("## Errors")
        lines.append("")
        for c in errors:
            lines.append(f"- **{c.case_id}**: `{c.error}`")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="Run only the first N cases")
    parser.add_argument("--filter", type=str, default=None, help="Run cases whose category contains this string")
    parser.add_argument(
        "--cases",
        type=str,
        default=None,
        help="Comma-separated list of case ids to run (e.g. analyst-sector-exposure,research-single-ticker)",
    )
    args = parser.parse_args()
    case_ids = [c.strip() for c in args.cases.split(",")] if args.cases else None
    asyncio.run(main_async(args.limit, args.filter, case_ids))


if __name__ == "__main__":
    main()
