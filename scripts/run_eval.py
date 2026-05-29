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

DATASET_PATH = Path(__file__).parent.parent / "tests" / "eval_dataset.json"
RESULTS_PATH = Path(__file__).parent.parent / "tests" / "eval_results.json"


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
            if m.content and not m.tool_calls:
                content_chunks.append(m.content)
        elif isinstance(m, ToolMessage):
            tname = getattr(m, "name", None)
            if tname and tname not in tools:
                tools.append(tname)
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


async def _run_case(graph, case: dict) -> CaseScore:
    start = time.perf_counter()
    try:
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=case["question"])]}
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

    RESULTS_PATH.write_text(
        json.dumps(
            {"summary": avg, "cases": [asdict(r) for r in results]},
            indent=2,
        ),
        encoding="utf-8",
    )
    console.print(f"\n[dim]Wrote {RESULTS_PATH.relative_to(Path.cwd())}[/dim]")


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
