"""CLI entry point — typer + rich."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="aap-evals", help="AAP benchmarks and evaluations.")
console = Console()

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


# ── generate ───────────────────────────────────────────────────────────


def _build_prompt(cat, variant_idx: int) -> str:
    from .markers import marker_example

    variant = cat.variants[variant_idx % len(cat.variants)]
    me = marker_example(cat.fmt)
    sections_instruction = ""
    if cat.sections and me:
        section_list = ", ".join(cat.sections)
        sections_instruction = (
            f"\nWrap each major section with markers using EXACTLY this syntax: {me}\n"
            f"Replace ID with the section name.\n\n"
            f"You MUST include these section IDs: {section_list}\n"
        )
    return (
        f"{cat.prompt_base} {variant}.\n\n"
        f"Requirements:\n"
        f"- Self-contained, realistic, production-quality code/content\n"
        f"- At least 80 lines of meaningful content\n"
        f"- Use diverse, realistic data values (names, numbers, strings)\n"
        f"{sections_instruction}\n"
        f"Output ONLY the raw {cat.ext} content. No markdown fences, no explanation, no commentary."
    )


@app.command()
def generate(
    output: Annotated[Path, typer.Option(help="Output directory")] = DATA_DIR / "apply-engine",
    model: Annotated[str, typer.Option(help="Ollama model")] = "gemma4",
    host: Annotated[str, typer.Option(help="Ollama host")] = "http://localhost:11434",
    count: Annotated[int, typer.Option(help="Number of test cases (0 = all)")] = 0,
) -> None:
    """Generate benchmark corpus — artifacts via Ollama + deterministic envelopes."""
    from datetime import datetime, timezone

    from .agents import create_model, generate_artifact
    from .categories import CATEGORIES
    from .envelopes import generate_all_envelopes
    from .markers import extract_section_content

    llm = create_model("ollama", model, host)

    # Auto-increment from highest existing case number
    output.mkdir(parents=True, exist_ok=True)
    existing = [int(d.name[:4]) for d in output.iterdir() if d.is_dir() and d.name[:4].isdigit()]
    start_num = max(existing, default=0) + 1

    # Build flat task list
    tasks: list[tuple] = []
    cn = start_num
    for cat in CATEGORIES:
        for vi in range(cat.count):
            tasks.append((cat, vi, cn))
            cn += 1
    if count > 0:
        tasks = tasks[:count]

    total = len(tasks)
    console.print(f"Generating {total} test cases -> {output}/")
    console.print(f"Model: [bold]{model}[/bold] | Starting at case {start_num}\n")

    succeeded = 0
    failed = 0

    for cat, vi, cn in tasks:
        case_dir = output / f"{cn:04d}"
        artifact_id = f"artifact-{cn:04d}"
        prompt_text = _build_prompt(cat, vi)
        system_prompt = "You are a code generator. Output only raw code/content. No markdown fences, no explanation."

        try:
            content = generate_artifact(llm, prompt_text)
            if len(content) < 50:
                raise RuntimeError("artifact too short")
        except Exception as e:
            console.print(f"  [red]FAIL {cn:04d} ({cat.name}): {e}[/red]")
            failed += 1
            continue

        # Write artifact
        (case_dir / "artifacts").mkdir(parents=True, exist_ok=True)
        (case_dir / "artifacts" / cat.filename).write_text(content)

        # Generate and write envelopes
        all_envs = generate_all_envelopes(content, artifact_id, cat.fmt, cat.sections)
        (case_dir / "envelopes").mkdir(parents=True, exist_ok=True)
        for filename, envs in all_envs.items():
            with open(case_dir / "envelopes" / filename, "w") as f:
                for env in envs:
                    f.write(json.dumps(env, separators=(",", ":")) + "\n")

        valid_sections = [
            s for s in cat.sections
            if extract_section_content(content, s, cat.fmt) is not None
        ]

        # metadata.yml
        variant_desc = cat.variants[vi % len(cat.variants)]
        meta = "\n".join([
            f"case_num: {cn}", f"category: {cat.name}", f"variant: {variant_desc}",
            f"format: {cat.fmt}", f"extension: {cat.ext}", f"filename: {cat.filename}",
            f"model: {model}", f"host: {host}",
            f"generated_at: {datetime.now(timezone.utc).isoformat()}",
            f"artifact_bytes: {len(content.encode())}",
            f"sections_expected: [{', '.join(cat.sections)}]",
            f"sections_found: [{', '.join(valid_sections)}]",
            f"envelope_files: [{', '.join(sorted(all_envs.keys()))}]",
        ])
        (case_dir / "metadata.yml").write_text(meta + "\n")

        # prompt.md
        (case_dir / "prompt.md").write_text(
            f"# Case {cn:04d}: {cat.name} — {variant_desc}\n\n"
            f"**Model:** `{model}` | **Format:** `{cat.fmt}`\n\n"
            f"**Sections expected:** {', '.join(f'`{s}`' for s in cat.sections) or 'none'}\n"
            f"**Sections found:** {', '.join(f'`{s}`' for s in valid_sections) or 'none'}\n\n"
            f"## System Prompt\n\n```\n{system_prompt}\n```\n\n"
            f"## User Prompt\n\n```\n{prompt_text}\n```\n"
        )

        succeeded += 1
        if succeeded % 10 == 0 or succeeded == total:
            console.print(f"  [{succeeded}/{total}] {succeeded} ok, {failed} failed")

    console.print(f"\n[green]Done: {succeeded}/{total} succeeded, {failed} failed[/green]")


# ── experiment ─────────────────────────────────────────────────────────


@app.command()
def experiment(
    corpus: Annotated[Path, typer.Option(help="Corpus directory")] = DATA_DIR / "apply-engine",
    output: Annotated[Path, typer.Option(help="Results JSONL")] = DATA_DIR / "experiments" / "results.jsonl",
    provider: Annotated[str, typer.Option(help="LLM provider")] = "ollama",
    model: Annotated[str, typer.Option(help="Model name")] = "gemma4",
    host: Annotated[str, typer.Option(help="Ollama host")] = "http://localhost:11434",
    count: Annotated[int, typer.Option(help="Max test cases (0 = all)")] = 0,
) -> None:
    """Run baseline vs AAP experiment on corpus artifacts. Writes results incrementally."""
    from .agents import AAPResult, BaselineResult, create_model, run_aap, run_baseline

    llm = create_model(provider, model, host)
    meta_files = sorted(corpus.glob("*/metadata.yml"))
    if count > 0:
        meta_files = meta_files[:count]

    if not meta_files:
        console.print("[red]No test cases found. Run generate first.[/red]")
        raise typer.Exit(1)

    output.parent.mkdir(parents=True, exist_ok=True)
    console.print(f"Running {len(meta_files)} experiment(s) with [bold]{model}[/bold]\n")

    with open(output, "a") as results_file:
        for mf in meta_files:
            case_dir = mf.parent
            meta_text = mf.read_text()
            meta = {}
            for line in meta_text.split("\n"):
                if ": " in line and not line.startswith(" "):
                    key, val = line.split(": ", 1)
                    meta[key.strip()] = val.strip()

            fmt = meta.get("format", "text/html")
            category = meta.get("category", "")
            variant = meta.get("variant", "")
            prompt_md = case_dir / "prompt.md"

            if not prompt_md.exists():
                continue

            # Extract creation prompt from prompt.md
            prompt_content = prompt_md.read_text()
            # Get user prompt section
            user_prompt = ""
            in_user_prompt = False
            for line in prompt_content.split("\n"):
                if line.startswith("## User Prompt"):
                    in_user_prompt = True
                    continue
                if in_user_prompt and line == "```":
                    if user_prompt:
                        break
                    continue
                if in_user_prompt:
                    user_prompt += line + "\n"

            if not user_prompt.strip():
                continue

            # Simple edit prompts derived from the artifact
            edit_prompts = [
                "Change the primary heading text to 'Updated Dashboard'",
                "Update the first numeric value you find to 99999",
            ]

            console.print(f"[bold]{case_dir.name}[/bold] ({category})")

            # Run baseline
            try:
                baseline = run_baseline(llm, user_prompt.strip(), edit_prompts, fmt)
            except Exception as e:
                console.print(f"  [red]baseline failed: {e}[/red]")
                baseline = BaselineResult()

            # Run AAP
            try:
                aap = run_aap(llm, user_prompt.strip(), edit_prompts, fmt, f"artifact-{meta.get('case_num', 0)}")
            except Exception as e:
                console.print(f"  [red]AAP failed: {e}[/red]")
                aap = AAPResult()

            # Compute comparison
            savings_out = 0.0
            if baseline.total_output_tokens > 0:
                savings_out = 100 * (baseline.total_output_tokens - aap.total_output_tokens) / baseline.total_output_tokens

            result = {
                "case": case_dir.name,
                "category": category,
                "variant": variant,
                "format": fmt,
                "model": model,
                "baseline": {
                    "total_input_tokens": baseline.total_input_tokens,
                    "total_output_tokens": baseline.total_output_tokens,
                    "total_latency_ms": baseline.total_latency_ms,
                    "turns": [t.to_dict() for t in baseline.turns],
                },
                "aap": {
                    "total_input_tokens": aap.total_input_tokens,
                    "total_output_tokens": aap.total_output_tokens,
                    "total_latency_ms": aap.total_latency_ms,
                    "parse_rate": aap.parse_rate,
                    "apply_rate": aap.apply_rate,
                    "turns": [t.to_dict() for t in aap.turns],
                },
                "comparison": {
                    "output_token_savings_pct": round(savings_out, 1),
                },
            }

            results_file.write(json.dumps(result) + "\n")
            results_file.flush()

            tag = f"[green]{savings_out:.1f}% savings[/green]" if savings_out > 0 else f"[red]{savings_out:.1f}%[/red]"
            console.print(
                f"  baseline: {baseline.total_output_tokens} out tokens | "
                f"AAP: {aap.total_output_tokens} out tokens | "
                f"{tag} | parse: {aap.parse_rate:.0%} apply: {aap.apply_rate:.0%}"
            )

    console.print(f"\n[green]Results appended to {output}[/green]")


# ── run (conversation benchmark experiments) ──────────────────────────


FORMAT_TO_EXT = {
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
    """Extract format and extension from experiment README.md."""
    text = readme_path.read_text()
    for line in text.split("\n"):
        if "**Format:**" in line:
            # e.g. **Format:** text/html | **Size:** large | **Edits:** 4
            fmt = line.split("**Format:**")[1].split("|")[0].strip()
            ext = FORMAT_TO_EXT.get(fmt, ".txt")
            return fmt, ext
    return "text/html", ".html"


def _find_turn_files(input_dir: Path) -> list[Path]:
    """Find turn-N.md files sorted by turn number."""
    turns = sorted(input_dir.glob("turn-*.md"), key=lambda p: int(p.stem.split("-")[1]))
    return turns


@app.command(name="run")
def run_experiments(
    experiments_dir: Annotated[Path, typer.Option(help="Experiments directory")] = DATA_DIR / "experiments",
    provider: Annotated[str, typer.Option(help="LLM provider")] = "ollama",
    model: Annotated[str, typer.Option(help="Model name")] = "gemma4",
    host: Annotated[str, typer.Option(help="Ollama host")] = "http://localhost:11434",
    count: Annotated[int, typer.Option(help="Max experiments (0 = all)")] = 0,
    experiment_id: Annotated[str, typer.Option("--id", help="Run single experiment by prefix")] = "",
) -> None:
    """Run conversation benchmark experiments (base vs AAP flows)."""
    import time
    from datetime import datetime, timezone

    from pydantic_ai import Agent

    from .agents import clean_artifact, create_model
    from .apply import apply_envelope
    from .schema import Envelope

    llm = create_model(provider, model, host)

    # Find experiment directories
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

    console.print(f"Running {len(exp_dirs)} experiment(s) with [bold]{model}[/bold]\n")

    for exp_dir in exp_dirs:
        exp_name = exp_dir.name
        fmt, ext = _parse_experiment_format(exp_dir / "README.md")
        console.print(f"[bold]{exp_name}[/bold] ({fmt})")

        base_input = exp_dir / "inputs" / "base"
        aap_input = exp_dir / "inputs" / "aap"
        base_output = exp_dir / "outputs" / "base"
        aap_output = exp_dir / "outputs" / "aap"
        base_output.mkdir(parents=True, exist_ok=True)
        aap_output.mkdir(parents=True, exist_ok=True)

        # Read prompts
        base_system = (base_input / "system.md").read_text().strip()
        init_system = (aap_input / "init-system.md").read_text().strip()
        maintain_system = (aap_input / "maintain-system.md").read_text().strip()
        turn_files = _find_turn_files(base_input)

        if not turn_files:
            console.print("  [yellow]no turn files, skipping[/yellow]")
            continue

        turn_0_prompt = turn_files[0].read_text().strip()
        edit_prompts = [(tf.stem, tf.read_text().strip()) for tf in turn_files[1:]]

        metrics: dict = {
            "experiment_id": exp_name,
            "model": model,
            "provider": provider,
            "seed": 42,
            "temperature": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "format": fmt,
        }

        # ── Shared Turn 0 ────────────────────────────────────────────
        base_agent: Agent[None, str] = Agent(llm, system_prompt=base_system)

        t0 = time.perf_counter()
        r = base_agent.run_sync(turn_0_prompt)
        turn0_ms = int((time.perf_counter() - t0) * 1000)
        turn0_usage = r.usage()
        shared_artifact = clean_artifact(r.output)

        # Save shared turn 0
        (base_output / f"turn-0{ext}").write_text(shared_artifact)
        (aap_output / f"turn-0{ext}").write_text(shared_artifact)

        metrics["shared"] = {
            "creation_input_tokens": turn0_usage.input_tokens,
            "creation_output_tokens": turn0_usage.output_tokens,
            "creation_latency_ms": turn0_ms,
            "artifact_bytes": len(shared_artifact.encode()),
        }

        console.print(f"  turn-0: {turn0_usage.output_tokens} out tokens, {turn0_ms}ms")

        # ── Base Flow (growing conversation) ──────────────────────────
        base_turns = []
        history = r.all_messages()
        base_artifact = shared_artifact

        for turn_name, edit_prompt in edit_prompts:
            t0 = time.perf_counter()
            r = base_agent.run_sync(edit_prompt, message_history=history)
            ms = int((time.perf_counter() - t0) * 1000)
            usage = r.usage()
            history = r.all_messages()
            base_artifact = clean_artifact(r.output)

            turn_num = int(turn_name.split("-")[1])
            (base_output / f"{turn_name}{ext}").write_text(base_artifact)

            base_turns.append({
                "turn": turn_num,
                "edit": edit_prompt[:80],
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "latency_ms": ms,
                "output_bytes": len(base_artifact.encode()),
            })

            console.print(
                f"  base {turn_name}: {usage.output_tokens} out, "
                f"{usage.input_tokens} in, {ms}ms"
            )

        base_total_in = sum(t["input_tokens"] for t in base_turns)
        base_total_out = sum(t["output_tokens"] for t in base_turns)
        base_total_ms = sum(t["latency_ms"] for t in base_turns)

        metrics["default_flow"] = {
            "system_prompt_tokens": turn0_usage.input_tokens,
            "per_turn": base_turns,
            "total_input_tokens": base_total_in,
            "total_output_tokens": base_total_out,
            "total_latency_ms": base_total_ms,
        }

        # ── AAP Flow (stateless dispatch) ─────────────────────────────
        maintain_agent: Agent[None, Envelope] = Agent(
            llm,
            system_prompt=maintain_system,
            output_type=Envelope,
        )

        aap_turns = []
        aap_artifact = shared_artifact
        version = 1
        parse_successes = 0
        apply_successes = 0

        for turn_name, edit_prompt in edit_prompts:
            turn_num = int(turn_name.split("-")[1])
            user_msg = (
                f"## Current Artifact\n\n```\n{aap_artifact}\n```\n\n"
                f"## Edit Instruction\n\n{edit_prompt}"
            )

            t0 = time.perf_counter()
            parsed = False
            succeeded = False
            env_name = ""
            envelope_json = ""

            try:
                r = maintain_agent.run_sync(user_msg)
                ms = int((time.perf_counter() - t0) * 1000)
                usage = r.usage()

                envelope: Envelope = r.output
                parsed = True
                parse_successes += 1
                env_name = envelope.name
                envelope_json = envelope.model_dump_json(indent=2)

                new_artifact = apply_envelope(
                    aap_artifact, envelope.name, envelope.content, fmt,
                )
                succeeded = True
                apply_successes += 1
                aap_artifact = new_artifact
                version += 1

            except Exception as e:
                ms = int((time.perf_counter() - t0) * 1000)
                usage = type("U", (), {"input_tokens": 0, "output_tokens": 0})()
                console.print(f"  [red]aap {turn_name} failed: {e}[/red]")

            # Save outputs
            if envelope_json:
                (aap_output / f"{turn_name}.json").write_text(envelope_json)
            (aap_output / f"{turn_name}{ext}").write_text(aap_artifact)

            aap_turns.append({
                "turn": turn_num,
                "edit": edit_prompt[:80],
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "latency_ms": ms,
                "output_bytes": len(aap_artifact.encode()),
                "envelope_parsed": parsed,
                "apply_succeeded": succeeded,
                "envelope_name": env_name,
            })

            status = "[green]ok[/green]" if succeeded else "[red]fail[/red]"
            console.print(
                f"  aap  {turn_name}: {usage.output_tokens} out, "
                f"{usage.input_tokens} in, {ms}ms, {env_name} {status}"
            )

        num_edits = len(edit_prompts)
        aap_total_in = sum(t["input_tokens"] for t in aap_turns)
        aap_total_out = sum(t["output_tokens"] for t in aap_turns)
        aap_total_ms = sum(t["latency_ms"] for t in aap_turns)

        metrics["aap_flow"] = {
            "system_prompt_tokens": 0,
            "per_turn": aap_turns,
            "total_input_tokens": aap_total_in,
            "total_output_tokens": aap_total_out,
            "total_latency_ms": aap_total_ms,
            "envelope_parse_rate": parse_successes / num_edits if num_edits else 0,
            "apply_success_rate": apply_successes / num_edits if num_edits else 0,
        }

        # ── Comparison ────────────────────────────────────────────────
        out_savings = (
            100 * (base_total_out - aap_total_out) / base_total_out
            if base_total_out > 0 else 0
        )
        in_savings = (
            100 * (base_total_in - aap_total_in) / base_total_in
            if base_total_in > 0 else 0
        )
        latency_savings = (
            100 * (base_total_ms - aap_total_ms) / base_total_ms
            if base_total_ms > 0 else 0
        )

        metrics["comparison"] = {
            "output_token_savings_pct": round(out_savings, 1),
            "input_token_savings_pct": round(in_savings, 1),
            "latency_savings_pct": round(latency_savings, 1),
        }

        # Write metrics
        (exp_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")

        tag = f"[green]{out_savings:.1f}% out savings[/green]" if out_savings > 0 else f"[red]{out_savings:.1f}%[/red]"
        console.print(
            f"  [bold]summary:[/bold] base={base_total_out} out | aap={aap_total_out} out | "
            f"{tag} | parse={parse_successes}/{num_edits} apply={apply_successes}/{num_edits}\n"
        )

    console.print("[green]Done.[/green]")


# ── report ─────────────────────────────────────────────────────────────


@app.command()
def report(
    results_path: Annotated[Path, typer.Option("--input", help="Results JSONL")] = DATA_DIR / "experiments" / "results.jsonl",
    output: Annotated[Path, typer.Option(help="Markdown output")] = DATA_DIR / "experiments" / "results.md",
) -> None:
    """Generate markdown report from experiment results."""
    if not results_path.exists():
        console.print("[red]No results found. Run experiment first.[/red]")
        raise typer.Exit(1)

    results = [json.loads(line) for line in results_path.read_text().strip().split("\n") if line]

    if not results:
        console.print("[red]Empty results file.[/red]")
        raise typer.Exit(1)

    lines = [
        "# AAP Experiment Results\n",
        f"**Model:** `{results[0].get('model', 'unknown')}` | **Cases:** {len(results)}\n",
        "| Case | Category | Baseline Out | AAP Out | Savings | Parse | Apply |",
        "|------|----------|-------------:|--------:|--------:|------:|------:|",
    ]

    total_baseline = 0
    total_aap = 0

    for r in results:
        b = r["baseline"]
        a = r["aap"]
        c = r["comparison"]
        total_baseline += b["total_output_tokens"]
        total_aap += a["total_output_tokens"]
        lines.append(
            f"| {r['case'][:20]} | {r['category']} | "
            f"{b['total_output_tokens']} | {a['total_output_tokens']} | "
            f"{c['output_token_savings_pct']}% | "
            f"{a['parse_rate']:.0%} | {a['apply_rate']:.0%} |"
        )

    overall_savings = 100 * (total_baseline - total_aap) / total_baseline if total_baseline > 0 else 0
    lines.append(f"\n**Overall output token savings: {overall_savings:.1f}%**\n")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")
    console.print(f"[green]Report written to {output}[/green]")
