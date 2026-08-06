from __future__ import annotations

import json
import shutil
from importlib import resources
from pathlib import Path
from typing import Annotated, Any

import typer
import yaml
from rich.console import Console
from rich.table import Table

from glyphprobe import __version__
from glyphprobe.backends.registry import create_backend, default_base_url
from glyphprobe.capabilities import Capability, CapabilityReport
from glyphprobe.config import (
    EmojiItem,
    ExperimentConfig,
    ResolvedInputs,
    apply_cli_overrides,
    load_experiment_config,
)
from glyphprobe.errors import GlyphProbeError
from glyphprobe.experiment.plan import build_plan
from glyphprobe.experiment.runner import run_experiment
from glyphprobe.io import read_yaml, write_json
from glyphprobe.reporting import render_markdown_report

app = typer.Typer(
    name="glyphprobe",
    no_args_is_help=True,
    add_completion=False,
    help="Emoji/glyph activation cartography with explicit backend capability boundaries.",
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"glyphprobe {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the GlyphProbe package version and exit.",
    ),
) -> None:
    del version


def _parse_glyphs(
    raw: str | list[str] | None,
    path: Path | None,
) -> list[str | EmojiItem] | None:
    values: list[str | EmojiItem] = []
    if raw:
        if isinstance(raw, str):
            values.extend(part.strip() for part in raw.split(",") if part.strip())
        else:
            values.extend(str(part).strip() for part in raw if str(part).strip())
    if path:
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(text)
            if isinstance(data, dict):
                data = data.get("emojis", data.get("glyphs", data.get("items", [])))
            if not isinstance(data, list):
                raise typer.BadParameter("Emoji YAML must contain a list")
            for index, item in enumerate(data):
                if isinstance(item, dict):
                    payload = dict(item)
                    payload.setdefault("id", f"glyph_{index:02d}")
                    try:
                        values.append(EmojiItem.model_validate(payload))
                    except Exception as exc:
                        raise typer.BadParameter(
                            f"Invalid emoji panel item at index {index}: {exc}"
                        ) from exc
                else:
                    values.append(str(item))
        else:
            values.extend(line.strip() for line in text.splitlines() if line.strip())
    return values or None


def _replace_panel(
    cfg: ExperimentConfig,
    inputs: ResolvedInputs,
    glyphs: list[str | EmojiItem] | None,
) -> tuple[ExperimentConfig, ResolvedInputs]:
    if not glyphs:
        return cfg, inputs
    by_glyph = {item.glyph: item for item in inputs.panel_items}
    items: list[EmojiItem] = []
    for index, entry in enumerate(glyphs):
        if isinstance(entry, EmojiItem):
            items.append(entry)
            continue
        items.append(
            by_glyph.get(
                entry,
                EmojiItem(id=f"glyph_{index:02d}", glyph=entry, factors={}),
            )
        )
    ids = [item.id for item in items]
    raw_glyphs = [item.glyph for item in items]
    if len(ids) != len(set(ids)):
        raise typer.BadParameter("Override panel IDs must be unique")
    if len(raw_glyphs) != len(set(raw_glyphs)):
        raise typer.BadParameter("Override panel glyphs must be unique")
    data = cfg.model_dump(mode="python")
    data["panel"]["file"] = None
    data["panel"]["items"] = [item.model_dump(mode="python") for item in items]
    new_cfg = ExperimentConfig.model_validate(data)
    new_inputs = inputs.model_copy(update={"panel_items": items})
    return new_cfg, new_inputs


def _load_with_cli(
    config: Path,
    set_values: list[str],
    *,
    backend: str | None,
    model: str | None,
    base_url: str | None,
    device: str | None,
    dtype: str | None,
    emojis: str | None,
    emoji_file: Path | None,
    output_root: Path | None,
) -> tuple[ExperimentConfig, ResolvedInputs]:
    cfg, inputs = load_experiment_config(config, overrides=set_values)
    cfg = apply_cli_overrides(
        cfg,
        backend=backend,
        model=model,
        base_url=base_url,
        device=device,
        dtype=dtype,
        output_root=output_root,
    )
    glyphs = _parse_glyphs(emojis, emoji_file)
    return _replace_panel(cfg, inputs, glyphs)


def _resolved_backend_config(
    cfg: ExperimentConfig,
    inputs: ResolvedInputs,
) -> Any:
    if inputs.backend_validation_receipt is None:
        return cfg.backend
    return cfg.backend.model_copy(
        update={"validation_receipt": inputs.backend_validation_receipt}
    )


def _static_capabilities(cfg: ExperimentConfig) -> CapabilityReport:
    internal = cfg.backend.kind in {"mock", "transformers", "lens", "mlx"}
    caps = {
        cap: (
            cap
            in {
                Capability.TOKENIZE,
                Capability.GENERATE,
                Capability.FORWARD_LOGITS,
                Capability.HIDDEN_STATES,
                Capability.ACTIVATION_CACHE,
                Capability.ACTIVATION_PATCH,
                Capability.DETERMINISTIC_FORWARD,
            }
            if internal
            else cap == Capability.GENERATE
        )
        for cap in Capability
    }
    if cfg.backend.kind == "lens":
        caps[Capability.CANONICAL_HOOKS] = True
    if cfg.backend.kind == "mlx":
        caps[Capability.GENERATE] = False
        caps[Capability.ACTIVATION_PATCH] = bool(
            cfg.backend.validation_receipt and cfg.backend.validation_receipt_sha256
        )
    return CapabilityReport(
        backend=cfg.backend.kind,
        model=cfg.backend.model,
        capabilities=caps,
        notes={"status": "static pre-load estimate"},
    )


COMMON_CONFIG = Annotated[Path, typer.Option("--config", "-c", exists=True, dir_okay=False)]
COMMON_SET = Annotated[
    list[str],
    typer.Option("--set", help="Dotted config override, e.g. --set intervention.strengths='[0.02,0.05]'."),
]


@app.command()
def init(
    destination: Path = typer.Argument(Path("glyphprobe-experiment")),
    force: bool = typer.Option(
        False,
        "--force",
        help="Replace an existing destination directory.",
    ),
) -> None:
    """Copy sealed starter configs and data into a new experiment directory."""
    destination = destination.expanduser().resolve()
    if destination.exists():
        if not force:
            raise typer.BadParameter(
                f"Destination already exists: {destination}. Use --force to replace it."
            )
        if destination.is_dir():
            shutil.rmtree(destination)
        else:
            destination.unlink()
    source = resources.files("glyphprobe").joinpath("resources")
    with resources.as_file(source) as source_path:
        shutil.copytree(source_path, destination)
    console.print(f"[bold green]Initialized[/bold green]  {destination}")


@app.command("backends")
def list_backends() -> None:
    """Show backend presets and their honest intervention boundary."""
    table = Table(title="GlyphProbe backend capability map")
    table.add_column("Backend")
    table.add_column("Default URL")
    table.add_column("Internal activation patching")
    table.add_column("Primary role")
    roles = {
        "mock": (None, "yes (synthetic)", "CI/smoke only"),
        "transformers": (None, "yes", "raw PyTorch/HF hooks"),
        "lens": (None, "yes", "canonical TransformerLens hooks + SAE path"),
        "mlx": (None, "yes (resid_post)", "Apple-silicon MLX-LM probes"),
        "vllm": (default_base_url("vllm"), "no", "surface/server parity"),
        "llamacpp": (default_base_url("llamacpp"), "no", "GGUF surface/server parity"),
        "ollama": (default_base_url("ollama"), "no", "local surface/server parity"),
        "lmstudio": (default_base_url("lmstudio"), "no", "local surface/server parity"),
        "openai": ("client default", "no", "surface-only compatible endpoint"),
    }
    for name, (url, patching, role) in roles.items():
        table.add_row(name, url or "local process", patching, role)
    console.print(table)


@app.command()
def plan(
    config: COMMON_CONFIG,
    set_values: COMMON_SET = [],
    backend: str | None = typer.Option(None, "--backend", "-b"),
    model: str | None = typer.Option(None, "--model", "-m"),
    base_url: str | None = typer.Option(None, "--base-url"),
    device: str | None = typer.Option(None, "--device"),
    dtype: str | None = typer.Option(None, "--dtype"),
    emojis: str | None = typer.Option(None, "--emojis", help="Comma-separated glyph panel."),
    emoji_file: Path | None = typer.Option(None, "--emoji-file", exists=True, dir_okay=False),
    output_root: Path | None = typer.Option(None, "--output-root"),
    num_layers: int | None = typer.Option(
        None,
        "--num-layers",
        help="Avoid model loading by supplying the architecture layer count.",
    ),
    load_model: bool = typer.Option(False, "--load-model/--no-load-model"),
) -> None:
    """Resolve the experiment matrix and estimate calls before spending compute."""
    cfg, inputs = _load_with_cli(
        config,
        set_values,
        backend=backend,
        model=model,
        base_url=base_url,
        device=device,
        dtype=dtype,
        emojis=emojis,
        emoji_file=emoji_file,
        output_root=output_root,
    )
    backend_obj = None
    try:
        if load_model:
            backend_obj = create_backend(_resolved_backend_config(cfg, inputs))
            backend_obj.load()
            capabilities = backend_obj.capabilities()
            resolved_num_layers = backend_obj.num_layers
        else:
            capabilities = _static_capabilities(cfg)
            resolved_num_layers = num_layers
            if cfg.backend.kind == "mock" and resolved_num_layers is None:
                resolved_num_layers = 8
            if cfg.backend.kind in {"transformers", "lens", "mlx"} and resolved_num_layers is None:
                raise typer.BadParameter(
                    "Internal planning without model loading requires --num-layers"
                )
        plan_data = build_plan(
            cfg,
            inputs,
            capabilities,
            num_layers=resolved_num_layers,
        )
        console.print_json(json.dumps(plan_data, ensure_ascii=False))
    finally:
        if backend_obj is not None:
            backend_obj.close()


@app.command()
def doctor(
    backend: str = typer.Option(..., "--backend", "-b"),
    model: str = typer.Option(..., "--model", "-m"),
    base_url: str | None = typer.Option(None, "--base-url"),
    device: str = typer.Option("auto", "--device"),
    dtype: str = typer.Option("auto", "--dtype"),
) -> None:
    """Load or contact a backend and print its runtime capability receipt."""
    cfg = ExperimentConfig.model_validate(
        {
            "backend": {
                "kind": backend,
                "model": model,
                "base_url": base_url,
                "device": device,
                "dtype": dtype,
            },
            "panel": {"items": [{"id": "probe", "glyph": "🟤"}]},
            "source": {"wrappers_file": "unused.jsonl"},
            "targets": {"cases_file": "unused.jsonl"},
        }
    )
    backend_obj = create_backend(cfg.backend)
    try:
        backend_obj.load()
        payload: dict[str, Any] = {
            "capabilities": backend_obj.capabilities().as_plain_dict(),
            "model_receipt": backend_obj.model_receipt(),
        }
        if hasattr(backend_obj, "probe"):
            payload["probe"] = backend_obj.probe()
            payload["capabilities_after_probe"] = backend_obj.capabilities().as_plain_dict()
        else:
            try:
                tokenization = backend_obj.tokenize("🟤")
                payload["tokenization_probe"] = {
                    "token_ids": tokenization.token_ids,
                    "tokens": tokenization.tokens,
                }
            except Exception as exc:
                payload["tokenization_probe_error"] = repr(exc)
        console.print_json(json.dumps(payload, ensure_ascii=False, default=str))
    finally:
        backend_obj.close()


@app.command()
def inspect(
    config: COMMON_CONFIG,
    set_values: COMMON_SET = [],
    backend: str | None = typer.Option(None, "--backend", "-b"),
    model: str | None = typer.Option(None, "--model", "-m"),
    device: str | None = typer.Option(None, "--device"),
    dtype: str | None = typer.Option(None, "--dtype"),
    emojis: str | None = typer.Option(None, "--emojis"),
    emoji_file: Path | None = typer.Option(None, "--emoji-file", exists=True, dir_okay=False),
) -> None:
    """Inspect the raw tokenization of a panel before any activation run."""
    cfg, inputs = _load_with_cli(
        config,
        set_values,
        backend=backend,
        model=model,
        base_url=None,
        device=device,
        dtype=dtype,
        emojis=emojis,
        emoji_file=emoji_file,
        output_root=None,
    )
    backend_obj = create_backend(_resolved_backend_config(cfg, inputs))
    try:
        backend_obj.load()
        table = Table(title=f"Tokenization: {cfg.backend.kind} / {cfg.backend.model}")
        table.add_column("ID")
        table.add_column("Glyph")
        table.add_column("Count")
        table.add_column("Token IDs")
        table.add_column("Tokens")
        for item in inputs.panel_items:
            record = backend_obj.tokenize(item.glyph)
            table.add_row(
                item.id,
                item.glyph,
                str(len(record.token_ids)),
                repr(record.token_ids),
                repr(record.tokens),
            )
        console.print(table)
    finally:
        backend_obj.close()


@app.command()
def run(
    config: COMMON_CONFIG,
    set_values: COMMON_SET = [],
    backend: str | None = typer.Option(None, "--backend", "-b"),
    model: str | None = typer.Option(None, "--model", "-m"),
    base_url: str | None = typer.Option(None, "--base-url"),
    device: str | None = typer.Option(None, "--device"),
    dtype: str | None = typer.Option(None, "--dtype"),
    emojis: str | None = typer.Option(None, "--emojis", help="Comma-separated glyph panel."),
    emoji_file: Path | None = typer.Option(None, "--emoji-file", exists=True, dir_okay=False),
    output_root: Path | None = typer.Option(None, "--output-root"),
) -> None:
    """Run one sealed panel × layer × strength × target matrix."""
    cfg, inputs = _load_with_cli(
        config,
        set_values,
        backend=backend,
        model=model,
        base_url=base_url,
        device=device,
        dtype=dtype,
        emojis=emojis,
        emoji_file=emoji_file,
        output_root=output_root,
    )
    try:
        run_dir, summary = run_experiment(cfg, inputs)
    except GlyphProbeError as exc:
        console.print(f"[bold red]GlyphProbe failed:[/bold red] {exc}")
        raise typer.Exit(code=2) from exc
    console.print(f"[bold green]Complete[/bold green]  {run_dir}")
    console.print_json(json.dumps(summary, ensure_ascii=False))


@app.command()
def matrix(
    matrix_file: Annotated[Path, typer.Option("--matrix", "-x", exists=True, dir_okay=False)],
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Run a backend/model/config matrix declared in YAML."""
    raw = read_yaml(matrix_file)
    base_config = Path(raw["base_config"])
    if not base_config.is_absolute():
        base_config = (matrix_file.parent / base_config).resolve()
    cells = raw.get("cells", [])
    if not isinstance(cells, list) or not cells:
        raise typer.BadParameter("Matrix YAML needs a non-empty cells list")
    outputs: list[dict[str, Any]] = []
    for index, cell in enumerate(cells):
        if not isinstance(cell, dict):
            raise typer.BadParameter(f"Cell {index} is not a mapping")
        overrides = [str(value) for value in cell.get("set", [])]
        cfg, inputs = _load_with_cli(
            base_config,
            overrides,
            backend=cell.get("backend"),
            model=cell.get("model"),
            base_url=cell.get("base_url"),
            device=cell.get("device"),
            dtype=cell.get("dtype"),
            emojis=cell.get("emojis"),
            emoji_file=(matrix_file.parent / cell["emoji_file"]).resolve()
            if cell.get("emoji_file")
            else None,
            output_root=(matrix_file.parent / cell["output_root"]).resolve()
            if cell.get("output_root")
            else None,
        )
        label = cell.get("name", f"cell-{index:02d}")
        if dry_run:
            outputs.append(
                {
                    "name": label,
                    "backend": cfg.backend.kind,
                    "model": cfg.backend.model,
                    "emoji_count": len(inputs.panel_items),
                }
            )
            continue
        run_dir, summary = run_experiment(cfg, inputs)
        outputs.append({"name": label, "run_dir": str(run_dir), "summary": summary})
    console.print_json(json.dumps(outputs, ensure_ascii=False, default=str))


@app.command("render-report")
def render_report(run_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False)]) -> None:
    """Regenerate report.md from a completed run's machine-readable artifacts."""
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    receipt = json.loads((run_dir / "receipt.json").read_text(encoding="utf-8"))
    path = render_markdown_report(run_dir, summary, receipt)
    console.print(path)
