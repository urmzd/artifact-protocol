"""CLI entry point — delegates to runner and eval services."""

from __future__ import annotations

import asyncio
import json
import sys
from importlib.metadata import version as _pkg_version
from pathlib import Path
from typing import Annotated

import typer
from pydantic_ai.models import Model
from rich.console import Console
from rich.table import Table

from gap.evals import DATA_DIR

app = typer.Typer(name="gap-evals", help="GAP benchmarks and evaluations.")
console = Console()


# ── version ───────────────────────────────────────────────────────────────


@app.command(name="version")
def show_version() -> None:
    """Print the installed gap-cli version."""
    try:
        v = _pkg_version("gap-cli")
    except Exception:
        v = "unknown"
    print(v)


# ── update ────────────────────────────────────────────────────────────────


@app.command(name="update")
def update_cli() -> None:
    """Update gap-cli to the latest published version."""
    import shutil
    import subprocess

    if shutil.which("uv"):
        cmd = ["uv", "tool", "upgrade", "gap-cli"]
    else:
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "gap-cli"]

    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
    result = subprocess.run(cmd)
    raise typer.Exit(result.returncode)

GAP_INIT_SPEC = (DATA_DIR / "gap-spec-init.md").read_text().strip()
GAP_MAINTAIN_SPEC = (DATA_DIR / "gap-spec-maintain.md").read_text().strip()

FORMAT_TO_EXT: dict[str, str] = {
    "text/html": ".html",
    "text/x-python": ".py",
    "application/javascript": ".js",
    "text/typescript": ".ts",
    "application/json": ".json",
    "text/x-yaml": ".yaml",
    "text/x-rust": ".rs",
    "text/x-go": ".go",
    "text/css": ".css",
    "application/x-sh": ".sh",
    "text/markdown": ".md",
    "image/svg+xml": ".svg",
    "application/toml": ".toml",
    "text/xml": ".xml",
    "text/x-java": ".java",
    "text/x-ruby": ".rb",
    "application/sql": ".sql",
}


def _parse_experiment_format(readme_path: Path) -> tuple[str, str]:
    text = readme_path.read_text()
    for line in text.split("\n"):
        if "**Format:**" in line:
            fmt = line.split("**Format:**")[1].split("|")[0].strip()
            ext = FORMAT_TO_EXT.get(fmt, ".txt")
            return fmt, ext
    return "text/html", ".html"


def _find_turn_files(input_dir: Path) -> list[Path]:
    return sorted(input_dir.glob("turn-*.md"), key=lambda p: int(p.stem.split("-")[1]))


def _build_token_table(metrics: dict) -> dict:
    """Build per-turn token comparison table."""
    turns = []

    # Turn 0
    bt0 = metrics.get("base_turn0", {})
    at0 = metrics.get("gap_turn0", {})
    turns.append({
        "turn": 0,
        "base_input": bt0.get("input_tokens", 0),
        "base_output": bt0.get("output_tokens", 0),
        "base_latency_ms": bt0.get("latency_ms", 0),
        "base_ttft_ms": bt0.get("ttft_ms"),
        "base_ttlt_ms": bt0.get("ttlt_ms"),
        "base_median_itl_ms": bt0.get("median_itl_ms"),
        "gap_input": at0.get("input_tokens", 0),
        "gap_output": at0.get("output_tokens", 0),
        "gap_latency_ms": at0.get("latency_ms", 0),
        "gap_ttft_ms": at0.get("ttft_ms"),
        "gap_ttlt_ms": at0.get("ttlt_ms"),
        "gap_median_itl_ms": at0.get("median_itl_ms"),
    })

    # Edit turns — zip base and GAP per_turn lists
    base_turns = metrics.get("default_flow", {}).get("per_turn", [])
    gap_turns = metrics.get("gap_flow", {}).get("per_turn", [])
    for bt, at in zip(base_turns, gap_turns):
        turns.append({
            "turn": bt.get("turn", 0),
            "base_input": bt.get("input_tokens", 0),
            "base_output": bt.get("output_tokens", 0),
            "base_latency_ms": bt.get("latency_ms", 0),
            "base_ttft_ms": bt.get("ttft_ms"),
            "base_ttlt_ms": bt.get("ttlt_ms"),
            "base_median_itl_ms": bt.get("median_itl_ms"),
            "gap_input": at.get("input_tokens", 0),
            "gap_output": at.get("output_tokens", 0),
            "gap_latency_ms": at.get("latency_ms", 0),
            "gap_ttft_ms": at.get("ttft_ms"),
            "gap_ttlt_ms": at.get("ttlt_ms"),
            "gap_median_itl_ms": at.get("median_itl_ms"),
            "envelope_name": at.get("envelope_name", ""),
            "apply_ok": at.get("apply_succeeded", False),
        })

    # Totals
    total_bi = sum(t["base_input"] for t in turns)
    total_bo = sum(t["base_output"] for t in turns)
    total_ai = sum(t["gap_input"] for t in turns)
    total_ao = sum(t["gap_output"] for t in turns)
    total_bms = sum(t["base_latency_ms"] for t in turns)
    total_ams = sum(t["gap_latency_ms"] for t in turns)

    return {
        "turns": turns,
        "totals": {
            "base_input": total_bi,
            "base_output": total_bo,
            "base_combined": total_bi + total_bo,
            "gap_input": total_ai,
            "gap_output": total_ao,
            "gap_combined": total_ai + total_ao,
            "base_latency_ms": total_bms,
            "gap_latency_ms": total_ams,
            "output_savings_pct": round(100 * (total_bo - total_ao) / total_bo, 1) if total_bo else 0,
            "input_delta_pct": round(100 * (total_ai - total_bi) / total_bi, 1) if total_bi else 0,
            "combined_savings_pct": round(
                100 * ((total_bi + total_bo) - (total_ai + total_ao)) / (total_bi + total_bo), 1
            ) if (total_bi + total_bo) else 0,
            "latency_savings_pct": round(100 * (total_bms - total_ams) / total_bms, 1) if total_bms else 0,
        },
    }


async def _run_single_experiment(
    llm: Model,
    provider_name: str,
    model_name: str,
    exp_dir: Path,
    flow: str,
    skip_eval: bool,
) -> bool:
    """Run a single experiment (base vs GAP flows). Returns True on success."""
    from datetime import datetime, timezone

    from gap.evals.eval.metrics import score_experiment
    from gap.evals.runner.gap import run_gap_flow, run_gap_turn0
    from gap.evals.runner.base import run_base_flow, run_base_turn0

    exp_name = exp_dir.name
    fmt, ext = _parse_experiment_format(exp_dir / "README.md")

    if (exp_dir / "metrics.json").exists():
        console.print(f"[dim]{exp_name} — already done, skipping[/dim]")
        return True

    console.print(f"[bold]{exp_name}[/bold] ({fmt}) via [cyan]{provider_name}[/cyan]")
    try:
        base_input = exp_dir / "inputs" / "base"
        base_output = exp_dir / "outputs" / "base"
        gap_output = exp_dir / "outputs" / "gap"
        base_output.mkdir(parents=True, exist_ok=True)
        gap_output.mkdir(parents=True, exist_ok=True)

        base_system = (base_input / "system.md").read_text().strip()
        init_system = base_system + "\n\n" + GAP_INIT_SPEC
        maintain_system = base_system + "\n\n" + GAP_MAINTAIN_SPEC
        turn_files = _find_turn_files(base_input)

        if not turn_files:
            console.print(f"  [yellow]{exp_name}: no turn files, skipping[/yellow]")
            return True

        turn_0_prompt = turn_files[0].read_text().strip()
        edit_prompts = [(tf.stem, tf.read_text().strip()) for tf in turn_files[1:]]

        metrics: dict = {
            "experiment_id": exp_name,
            "model": model_name,
            "provider": provider_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "format": fmt,
        }

        # ── Turn 0 ───────────────────────────────────────────────
        history = []
        base_art = ""
        gap_art = ""

        if flow in ("base", "both"):
            base_art, history, bt0 = await run_base_turn0(llm, base_system, turn_0_prompt, base_output, ext)
            metrics["base_turn0"] = bt0
            ttft = f", ttft={bt0['ttft_ms']}ms" if bt0.get('ttft_ms') is not None else ""
            console.print(f"  [{provider_name}] {exp_name} base turn-0: {bt0['output_tokens']} out, {bt0['latency_ms']}ms{ttft}")

        if flow in ("gap", "both"):
            gap_art, at0 = await run_gap_turn0(llm, init_system, turn_0_prompt, gap_output, ext)
            metrics["gap_turn0"] = at0
            ttft = f", ttft={at0['ttft_ms']}ms" if at0.get('ttft_ms') is not None else ""
            console.print(f"  [{provider_name}] {exp_name} gap  turn-0: {at0['output_tokens']} out, {at0['latency_ms']}ms{ttft}")

        # ── Base flow ─────────────────────────────────────────────
        if flow in ("base", "both") and edit_prompts:
            base_results, base_final = await run_base_flow(llm, base_system, history, edit_prompts, base_output, ext)
            base_total_out = sum(r.output_tokens for r in base_results)
            base_total_in = sum(r.input_tokens for r in base_results)
            base_total_ms = sum(r.latency_ms for r in base_results)

            metrics["default_flow"] = {
                "per_turn": [r.model_dump() for r in base_results],
                "total_input_tokens": base_total_in,
                "total_output_tokens": base_total_out,
                "total_latency_ms": base_total_ms,
            }

            for r in base_results:
                ttft = f", ttft={r.ttft_ms}ms" if r.ttft_ms is not None else ""
                console.print(f"  [{provider_name}] {exp_name} base turn-{r.turn}: {r.output_tokens} out, {r.input_tokens} in, {r.latency_ms}ms{ttft}")

        # ── GAP flow ──────────────────────────────────────────────
        parse_ok = 0
        apply_ok = 0
        num_edits = 0
        if flow in ("gap", "both") and edit_prompts:
            gap_results, gap_final = await run_gap_flow(llm, maintain_system, gap_art, edit_prompts, fmt, gap_output, ext)
            gap_total_out = sum(r.output_tokens for r in gap_results)
            gap_total_in = sum(r.input_tokens for r in gap_results)
            gap_total_ms = sum(r.latency_ms for r in gap_results)
            parse_ok = sum(1 for r in gap_results if r.envelope_parsed)
            apply_ok = sum(1 for r in gap_results if r.apply_succeeded)
            num_edits = len(gap_results)

            metrics["gap_flow"] = {
                "per_turn": [r.model_dump() for r in gap_results],
                "total_input_tokens": gap_total_in,
                "total_output_tokens": gap_total_out,
                "total_latency_ms": gap_total_ms,
                "envelope_parse_rate": parse_ok / num_edits if num_edits else 0,
                "apply_success_rate": apply_ok / num_edits if num_edits else 0,
            }

            for r in gap_results:
                status = "[green]ok[/green]" if r.apply_succeeded else "[red]fail[/red]"
                ttft = f", ttft={r.ttft_ms}ms" if r.ttft_ms is not None else ""
                console.print(
                    f"  [{provider_name}] {exp_name} gap  turn-{r.turn}: {r.output_tokens} out, {r.input_tokens} in, "
                    f"{r.latency_ms}ms{ttft}, {r.envelope_name} {status}"
                )

        # ── Comparison + token table ──────────────────────────────
        if "default_flow" in metrics and "gap_flow" in metrics:
            bo = metrics["default_flow"]["total_output_tokens"]
            ao = metrics["gap_flow"]["total_output_tokens"]
            bi = metrics["default_flow"]["total_input_tokens"]
            ai = metrics["gap_flow"]["total_input_tokens"]
            bms = metrics["default_flow"]["total_latency_ms"]
            ams = metrics["gap_flow"]["total_latency_ms"]

            metrics["comparison"] = {
                "output_token_savings_pct": round(100 * (bo - ao) / bo, 1) if bo else 0,
                "input_token_savings_pct": round(100 * (bi - ai) / bi, 1) if bi else 0,
                "latency_savings_pct": round(100 * (bms - ams) / bms, 1) if bms else 0,
            }
            metrics["token_table"] = _build_token_table(metrics)

            out_sav = metrics["comparison"]["output_token_savings_pct"]
            tag = f"[green]{out_sav:.1f}% out savings[/green]" if out_sav > 0 else f"[red]{out_sav:.1f}%[/red]"
            console.print(
                f"  [{provider_name}] [bold]{exp_name} summary:[/bold] base={bo} out | gap={ao} out | "
                f"{tag} | parse={parse_ok}/{num_edits} apply={apply_ok}/{num_edits}\n"
            )

        # ── Quality eval ──────────────────────────────────────────
        if not skip_eval and base_output.exists() and gap_output.exists():
            quality = score_experiment(base_output, gap_output, ext)
            if quality.per_turn:
                metrics["quality"] = quality.model_dump()
                console.print(
                    f"  [{provider_name}] {exp_name} [dim]quality: seq_sim={quality.mean_sequence_similarity:.3f} "
                    f"token_f1={quality.mean_token_f1:.3f}[/dim]"
                )

        (exp_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
        return True

    except Exception as e:
        console.print(f"  [{provider_name}] [red]{exp_name} FAILED: {e}[/red]\n")
        return False


# ── run ───────────────────────────────────────────────────────────────────


@app.command(name="run")
def run_experiments(
    experiments_dir: Annotated[Path, typer.Option(help="Experiments directory")] = DATA_DIR / "experiments",
    provider: Annotated[str, typer.Option(help="LLM provider (single)")] = "google",
    providers: Annotated[str, typer.Option(help="Comma-separated providers for parallel execution")] = "",
    model: Annotated[str, typer.Option(help="Model name (applies to single --provider only)")] = "",
    host: Annotated[str, typer.Option(help="Ollama host")] = "http://localhost:11434",
    fallback: Annotated[str, typer.Option(help="Fallback provider")] = "",
    count: Annotated[int, typer.Option(help="Max experiments (0=all)")] = 0,
    experiment_id: Annotated[str, typer.Option("--id", help="Run single experiment")] = "",
    flow: Annotated[str, typer.Option(help="Which flow: base, gap, both")] = "both",
    skip_eval: Annotated[bool, typer.Option(help="Skip quality eval")] = False,
) -> None:
    """Run conversation benchmark experiments (base vs GAP flows).

    Use --providers for parallel execution across multiple free-tier providers:
        gap-evals run --providers google,groq,github
    """
    asyncio.run(_run_experiments_async(
        experiments_dir, provider, providers, model, host, fallback,
        count, experiment_id, flow, skip_eval,
    ))


async def _run_experiments_async(
    experiments_dir: Path,
    provider: str,
    providers: str,
    model: str,
    host: str,
    fallback: str,
    count: int,
    experiment_id: str,
    flow: str,
    skip_eval: bool,
) -> None:
    from gap.evals.agents import PROVIDER_DEFAULTS, create_model

    # ── Build provider list ───────────────────────────────────────────
    if providers:
        provider_list = [p.strip() for p in providers.split(",") if p.strip()]
    else:
        provider_list = [provider]

    models: list[tuple[str, Model]] = []
    for prov in provider_list:
        m = model if len(provider_list) == 1 else ""
        llm = create_model(prov, m, host, fallback)
        models.append((prov, llm))

    # ── Collect experiment dirs ───────────────────────────────────────
    exp_dirs = sorted(
        d for d in experiments_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".") and d.name != "EXPERIMENT.md"
        and (d / "README.md").exists()
    )
    if experiment_id:
        exp_dirs = [d for d in exp_dirs if d.name.startswith(experiment_id)]
    if count > 0:
        exp_dirs = exp_dirs[:count]
    if not exp_dirs:
        console.print("[red]No experiments found.[/red]")
        raise typer.Exit(1)

    provider_labels = ", ".join(f"{p} ({PROVIDER_DEFAULTS.get(p, '?')})" for p in provider_list)
    console.print(
        f"Running {len(exp_dirs)} experiment(s) across {len(models)} provider(s): "
        f"[bold]{provider_labels}[/bold]\n"
    )

    # ── Sequential (single provider) ─────────────────────────────────
    if len(models) == 1:
        prov_name, llm = models[0]
        m_name = model or PROVIDER_DEFAULTS.get(prov_name, "")
        for exp_dir in exp_dirs:
            await _run_single_experiment(llm, prov_name, m_name, exp_dir, flow, skip_eval)
        console.print("[green]Done.[/green]")
        return

    # ── Parallel (multiple providers) ─────────────────────────────────
    provider_queues: dict[str, list[tuple[Path, Model, str]]] = {p: [] for p, _ in models}
    model_map = {p: llm for p, llm in models}
    for i, exp_dir in enumerate(exp_dirs):
        prov_name = provider_list[i % len(provider_list)]
        m_name = PROVIDER_DEFAULTS.get(prov_name, "")
        provider_queues[prov_name].append((exp_dir, model_map[prov_name], m_name))

    async def _run_provider_queue(prov_name: str, queue: list[tuple[Path, Model, str]]) -> tuple[int, int]:
        ok, fail = 0, 0
        for exp_dir, llm, m_name in queue:
            if await _run_single_experiment(llm, prov_name, m_name, exp_dir, flow, skip_eval):
                ok += 1
            else:
                fail += 1
        return ok, fail

    results = await asyncio.gather(*(
        _run_provider_queue(prov_name, queue)
        for prov_name, queue in provider_queues.items()
        if queue
    ))

    succeeded = sum(ok for ok, _ in results)
    failed = sum(fail for _, fail in results)
    console.print(
        f"\n[green]Done.[/green] {succeeded} succeeded, {failed} failed "
        f"across {len(models)} providers."
    )


# ── eval ──────────────────────────────────────────────────────────────────


@app.command(name="score")
def eval_experiments(
    experiments_dir: Annotated[Path, typer.Option(help="Experiments directory")] = DATA_DIR / "experiments",
    use_ragas: Annotated[bool, typer.Option(help="Use ragas for ROUGE-L and BLEU")] = False,
) -> None:
    """Score content quality for completed experiments (retroactive)."""
    from gap.evals.eval.metrics import score_experiment

    for exp_dir in sorted(experiments_dir.iterdir()):
        mf = exp_dir / "metrics.json"
        if not mf.exists():
            continue

        metrics = json.loads(mf.read_text())
        fmt = metrics.get("format", "text/html")
        ext = FORMAT_TO_EXT.get(fmt, ".txt")
        base_out = exp_dir / "outputs" / "base"
        gap_out = exp_dir / "outputs" / "gap"

        if not base_out.exists() or not gap_out.exists():
            continue

        quality = score_experiment(base_out, gap_out, ext, use_ragas)
        if quality.per_turn:
            metrics["quality"] = quality.model_dump()
            mf.write_text(json.dumps(metrics, indent=2) + "\n")
            console.print(
                f"{metrics['experiment_id']}: seq_sim={quality.mean_sequence_similarity:.3f} "
                f"f1={quality.mean_token_f1:.3f}"
            )


# ── report ────────────────────────────────────────────────────────────────


@app.command()
def report(
    experiments_dir: Annotated[Path, typer.Option(help="Experiments directory")] = DATA_DIR / "experiments",
    output: Annotated[Path, typer.Option(help="Output file")] = DATA_DIR / "experiments" / "results.md",
    format: Annotated[str, typer.Option(help="Output format: human or json")] = "human",
) -> None:
    """Generate report from experiment metrics."""
    metrics_files = sorted(experiments_dir.glob("*/metrics.json"))
    if not metrics_files:
        console.print("[red]No metrics found.[/red]")
        raise typer.Exit(1)

    results = [json.loads(mf.read_text()) for mf in metrics_files]

    if format == "json":
        rows = []
        for r in results:
            tt = r.get("token_table", {}).get("totals", {})
            comp = r.get("comparison", {})
            gap_flow = r.get("gap_flow", {})
            qual = r.get("quality", {})
            num_edits = len(gap_flow.get("per_turn", []))
            parse_ok = sum(1 for t in gap_flow.get("per_turn", []) if t.get("envelope_parsed"))
            apply_ok = sum(1 for t in gap_flow.get("per_turn", []) if t.get("apply_succeeded"))
            rows.append({
                "experiment_id": r["experiment_id"],
                "format": r.get("format", ""),
                "model": r.get("model", ""),
                "provider": r.get("provider", ""),
                "base_input": tt.get("base_input", 0),
                "base_output": tt.get("base_output", 0),
                "gap_input": tt.get("gap_input", 0),
                "gap_output": tt.get("gap_output", 0),
                "output_savings_pct": comp.get("output_token_savings_pct", 0),
                "combined_savings_pct": tt.get("combined_savings_pct", 0),
                "parse_ok": parse_ok,
                "apply_ok": apply_ok,
                "num_edits": num_edits,
                "mean_sequence_similarity": qual.get("mean_sequence_similarity"),
                "mean_token_f1": qual.get("mean_token_f1"),
            })
        print(json.dumps(rows, indent=2))
        return

    # ── Rich terminal table ───────────────────────────────────────────
    table = Table(title="GAP Experiment Results", show_lines=True)
    table.add_column("Experiment", max_width=32)
    table.add_column("Fmt", max_width=8)
    table.add_column("Base In", justify="right")
    table.add_column("Base Out", justify="right")
    table.add_column("GAP In", justify="right")
    table.add_column("GAP Out", justify="right")
    table.add_column("Out Δ", justify="right")
    table.add_column("Combined Δ", justify="right")
    table.add_column("Parse", justify="right")
    table.add_column("Apply", justify="right")
    table.add_column("Seq Sim", justify="right")
    table.add_column("F1", justify="right")

    agg = {"bo": 0, "ao": 0, "bi": 0, "ai": 0, "parse": 0, "apply": 0, "edits": 0}

    for r in results:
        tt = r.get("token_table", {}).get("totals", {})
        comp = r.get("comparison", {})
        gap_flow = r.get("gap_flow", {})
        qual = r.get("quality", {})
        num_edits = len(gap_flow.get("per_turn", []))

        bi = tt.get("base_input", 0)
        bo = tt.get("base_output", 0)
        ai = tt.get("gap_input", 0)
        ao = tt.get("gap_output", 0)
        out_sav = comp.get("output_token_savings_pct", 0)
        comb_sav = tt.get("combined_savings_pct", 0)
        parse_ok = sum(1 for t in gap_flow.get("per_turn", []) if t.get("envelope_parsed"))
        apply_ok = sum(1 for t in gap_flow.get("per_turn", []) if t.get("apply_succeeded"))
        seq_sim = qual.get("mean_sequence_similarity", "")
        f1 = qual.get("mean_token_f1", "")

        agg["bo"] += bo; agg["ao"] += ao; agg["bi"] += bi; agg["ai"] += ai
        agg["parse"] += parse_ok; agg["apply"] += apply_ok; agg["edits"] += num_edits

        out_style = "green" if out_sav > 0 else "red"
        comb_style = "green" if comb_sav > 0 else "red"

        table.add_row(
            r["experiment_id"][:32],
            r.get("format", "")[:8],
            f"{bi:,}", f"{bo:,}",
            f"{ai:,}", f"{ao:,}",
            f"[{out_style}]{out_sav:.1f}%[/{out_style}]",
            f"[{comb_style}]{comb_sav:.1f}%[/{comb_style}]",
            f"{parse_ok}/{num_edits}" if num_edits else "-",
            f"{apply_ok}/{num_edits}" if num_edits else "-",
            f"{seq_sim:.3f}" if seq_sim else "-",
            f"{f1:.3f}" if f1 else "-",
        )

    # Totals row
    total_out_sav = round(100 * (agg["bo"] - agg["ao"]) / agg["bo"], 1) if agg["bo"] else 0
    total_comb = agg["bi"] + agg["bo"]
    total_comb_sav = round(100 * (total_comb - (agg["ai"] + agg["ao"])) / total_comb, 1) if total_comb else 0

    table.add_row(
        "[bold]TOTAL[/bold]", "",
        f"[bold]{agg['bi']:,}[/bold]", f"[bold]{agg['bo']:,}[/bold]",
        f"[bold]{agg['ai']:,}[/bold]", f"[bold]{agg['ao']:,}[/bold]",
        f"[bold]{total_out_sav:.1f}%[/bold]",
        f"[bold]{total_comb_sav:.1f}%[/bold]",
        f"[bold]{agg['parse']}/{agg['edits']}[/bold]",
        f"[bold]{agg['apply']}/{agg['edits']}[/bold]",
        "", "",
    )

    console.print(table)

    # ── Markdown file ─────────────────────────────────────────────────
    lines = [
        "# GAP Experiment Results\n",
        f"**Model:** `{results[0].get('model', '')}` | **Provider:** `{results[0].get('provider', '')}` | "
        f"**Experiments:** {len(results)}\n",
        "| Experiment | Fmt | Base In | Base Out | GAP In | GAP Out | Out Δ | Comb Δ | Parse | Apply | Seq Sim | F1 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for r in results:
        tt = r.get("token_table", {}).get("totals", {})
        comp = r.get("comparison", {})
        gap_flow = r.get("gap_flow", {})
        qual = r.get("quality", {})
        num_edits = len(gap_flow.get("per_turn", []))
        parse_ok = sum(1 for t in gap_flow.get("per_turn", []) if t.get("envelope_parsed"))
        apply_ok = sum(1 for t in gap_flow.get("per_turn", []) if t.get("apply_succeeded"))

        lines.append(
            f"| {r['experiment_id'][:30]} | {r.get('format', '')[:8]} | "
            f"{tt.get('base_input', 0):,} | {tt.get('base_output', 0):,} | "
            f"{tt.get('gap_input', 0):,} | {tt.get('gap_output', 0):,} | "
            f"{comp.get('output_token_savings_pct', 0):.1f}% | "
            f"{tt.get('combined_savings_pct', 0):.1f}% | "
            f"{parse_ok}/{num_edits} | {apply_ok}/{num_edits} | "
            f"{qual.get('mean_sequence_similarity', ''):.3f} | "
            f"{qual.get('mean_token_f1', ''):.3f} |"
        )

    lines.extend(["", f"**Output savings:** {total_out_sav:.1f}% | "
        f"**Combined savings:** {total_comb_sav:.1f}% | "
        f"**Parse:** {agg['parse']}/{agg['edits']} | "
        f"**Apply:** {agg['apply']}/{agg['edits']}", ""])

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")
    console.print(f"\n[green]Written to {output}[/green]")


# ── eval ──────────────────────────────────────────────────────────────


@app.command(name="eval")
def evaluate(
    experiments_dir: Annotated[Path, typer.Option(help="Experiments directory")] = DATA_DIR / "experiments",
    provider: Annotated[str, typer.Option(help="LLM provider for judge")] = "",
    model: Annotated[str, typer.Option(help="Judge model name")] = "",
    host: Annotated[str, typer.Option(help="Ollama host")] = "http://localhost:11434",
    experiment_id: Annotated[str, typer.Option("--id", help="Eval single experiment by prefix")] = "",
    use_ragas: Annotated[bool, typer.Option(help="Include ROUGE-L and BLEU")] = False,
    judge: Annotated[bool, typer.Option(help="Enable LLM-as-judge scoring")] = False,
    count: Annotated[int, typer.Option(help="Max experiments (0 = all)")] = 0,
    force: Annotated[bool, typer.Option(help="Re-evaluate even if eval.json exists")] = False,
    format: Annotated[str, typer.Option(help="Output format: human or json")] = "human",
) -> None:
    """Evaluate output quality — text metrics and optional LLM-as-judge."""
    asyncio.run(_evaluate_async(
        experiments_dir, provider, model, host, experiment_id,
        use_ragas, judge, count, force, format,
    ))


async def _evaluate_async(
    experiments_dir: Path,
    provider: str,
    model: str,
    host: str,
    experiment_id: str,
    use_ragas: bool,
    judge: bool,
    count: int,
    force: bool,
    format: str = "human",
) -> None:
    from gap.evals.eval import run_eval

    judge_model = None
    if judge:
        if not provider:
            console.print("[red]--provider is required when using --judge[/red]")
            raise typer.Exit(1)
        from gap.evals.agents import create_model
        judge_model = create_model(provider, model, host)

    def _has_turn_outputs(d: Path) -> bool:
        base = d / "outputs" / "base"
        gap = d / "outputs" / "gap"
        return (
            base.is_dir() and gap.is_dir()
            and any(base.glob("turn-1*"))
            and any(gap.glob("turn-1*"))
        )

    exp_dirs = sorted(
        d for d in experiments_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
        and _has_turn_outputs(d)
    )

    if experiment_id:
        exp_dirs = [d for d in exp_dirs if d.name.startswith(experiment_id)]
    if count > 0:
        exp_dirs = exp_dirs[:count]
    if not exp_dirs:
        console.print("[red]No experiments with outputs found.[/red]")
        raise typer.Exit(1)

    if format != "json":
        console.print(f"Evaluating {len(exp_dirs)} experiment(s)" + (f" with judge ({model})" if judge else "") + "\n")

    table = Table(title="Eval Results")
    table.add_column("Experiment", style="bold")
    table.add_column("SeqSim", justify="right")
    table.add_column("TokenF1", justify="right")
    if judge:
        table.add_column("Base Judge", justify="right")
        table.add_column("GAP Judge", justify="right")

    json_rows: list[dict] = []

    for exp_dir in exp_dirs:
        exp_name = exp_dir.name
        eval_file = exp_dir / "eval.json"

        if eval_file.exists() and not force:
            if format != "json":
                console.print(f"[dim]{exp_name} — already evaluated, skipping[/dim]")
            continue

        fmt, ext = _parse_experiment_format(exp_dir / "README.md")

        try:
            quality = await run_eval(exp_dir, ext, use_ragas, judge_model)
            eval_file.write_text(quality.model_dump_json(indent=2) + "\n")

            if format == "json":
                row_dict: dict = {
                    "experiment_id": exp_name,
                    "mean_sequence_similarity": quality.mean_sequence_similarity,
                    "mean_token_f1": quality.mean_token_f1,
                }
                if judge:
                    row_dict["mean_base_judge"] = quality.mean_base_judge
                    row_dict["mean_gap_judge"] = quality.mean_gap_judge
                json_rows.append(row_dict)
            else:
                row = [
                    exp_name[:35],
                    f"{quality.mean_sequence_similarity:.3f}",
                    f"{quality.mean_token_f1:.3f}",
                ]
                if judge:
                    row.append(f"{quality.mean_base_judge:.3f}" if quality.mean_base_judge is not None else "—")
                    row.append(f"{quality.mean_gap_judge:.3f}" if quality.mean_gap_judge is not None else "—")
                table.add_row(*row)
                console.print(f"  [green]{exp_name}[/green] sim={quality.mean_sequence_similarity:.3f} f1={quality.mean_token_f1:.3f}")
        except Exception as e:
            if format != "json":
                console.print(f"  [red]{exp_name} failed: {e}[/red]")

    if format == "json":
        print(json.dumps(json_rows, indent=2))
    else:
        console.print()
        console.print(table)
        console.print("\n[green]Done.[/green]")
