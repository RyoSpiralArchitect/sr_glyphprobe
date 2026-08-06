from __future__ import annotations

from pathlib import Path
from typing import Any

from glyphprobe.io import atomic_write_text, read_jsonl


def _fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def render_markdown_report(run_dir: Path, summary: dict[str, Any], receipt: dict[str, Any]) -> Path:
    lines = [
        "# GlyphProbe v1 Pre-stage Run Report",
        "",
        f"**Run:** `{receipt.get('run_id', run_dir.name)}`  ",
        f"**Backend:** `{receipt.get('backend', {}).get('kind', 'unknown')}`  ",
        f"**Model:** `{receipt.get('backend', {}).get('model', 'unknown')}`  ",
        f"**Stage:** `{summary.get('stage')}`  ",
        f"**Causal claim authorized:** `{summary.get('causal_claim_authorized', False)}`  ",
        f"**Implementation hash:** `{receipt.get('implementation', {}).get('source_tree_sha256', 'unknown')}`",
        "",
        "The report is deliberately a pre-stage map. Stable differences may justify sharper causal tests, but they do not identify a semantic mechanism by themselves.",
        "",
        "## Run scale",
        "",
        f"- Emoji/glyphs: {_fmt(summary.get('emoji_count'))}",
        f"- Source wrappers: {_fmt(summary.get('wrapper_count'))}",
        f"- Target cases: {_fmt(summary.get('target_case_count'))}",
        f"- Replicate seeds: {_fmt(summary.get('seed_count'))}",
        f"- Intervention or observation records: {_fmt(summary.get('intervention_record_count', summary.get('observation_count')))}",
        f"- Errors: {_fmt(summary.get('error_count'))}",
        "",
    ]

    if summary.get("stage") == "pre-causal-activation-screen":
        lines.extend(
            [
                "## Principal pre-stage diagnostics",
                "",
                f"- Resolved layers: `{summary.get('resolved_layers')}`",
                f"- Median source-direction replicate alignment: {_fmt(summary.get('median_direction_replicate_alignment'))}",
                f"- Median emoji fingerprint advantage over random controls: {_fmt(summary.get('emoji_fingerprint_advantage'))}",
                f"- Median within-target label-permutation screening p: {_fmt(summary.get('median_emoji_label_permutation_p'))}",
                f"- Cross-seed fingerprint advantage over random controls: {_fmt(summary.get('cross_seed_fingerprint_advantage'))}",
                f"- Median maximum RMS-ratio matching error: {_fmt(summary.get('median_emoji_perturbation_ratio_max_abs_error'), 8)}",
                f"- Median KL dose monotonicity: {_fmt(summary.get('median_emoji_kl_dose_monotonicity'))}",
                f"- Median positive/negative fingerprint antisymmetry: {_fmt(summary.get('median_sign_antisymmetry'))}",
                f"- Maximum zero-hook logit-delta RMS: {_fmt(summary.get('zero_hook_max_logit_delta_rms'), 10)}",
                f"- Maximum zero-hook activation-delta RMS: {_fmt(summary.get('zero_hook_max_activation_delta_rms'), 10)}",
                f"- Raw glyph token counts: `{summary.get('glyph_token_counts')}`",
                f"- Wrapper token-count mismatch IDs: `{summary.get('wrapper_token_count_mismatch_ids')}`",
                f"- SAE analysis enabled: `{summary.get('sae_enabled')}`",
                f"- Iso-KL calibration enabled: `{summary.get('iso_kl_enabled')}`",
                "",
                "## Readiness gates",
                "",
            ]
        )
        readiness = summary.get("readiness", {})
        for check in readiness.get("checks", []):
            mark = "PASS" if check.get("pass") else "HOLD"
            lines.append(
                f"- **{mark}** `{check.get('id')}`: {_fmt(check.get('value'))}. {check.get('criterion')}"
            )
        lines.extend(
            [
                "",
                f"Passed {readiness.get('passed', 0)} of {readiness.get('total', 0)} gates.",
                "",
                "## Highest fingerprint separations",
                "",
            ]
        )
        rows = read_jsonl(run_dir / "fingerprint_summary.jsonl")
        rows = sorted(
            rows,
            key=lambda row: float(row.get("emoji_advantage_over_random") or float("-inf")),
            reverse=True,
        )
        for row in rows[:10]:
            lines.append(
                "- Layer {layer}, strength {strength}, seed {seed}: emoji separation {sep}; random separation {rnd}; advantage {adv}; label-permutation p {perm}; repeated-split 95% interval [{low}, {high}].".format(
                    layer=row.get("layer"),
                    strength=_fmt(row.get("strength"), 3),
                    seed=row.get("seed"),
                    sep=_fmt(row.get("emoji_separation")),
                    rnd=_fmt(row.get("random_separation")),
                    adv=_fmt(row.get("emoji_advantage_over_random")),
                    perm=_fmt(row.get("emoji_label_permutation_p")),
                    low=_fmt(row.get("emoji_split_repeat_ci_low")),
                    high=_fmt(row.get("emoji_split_repeat_ci_high")),
                )
            )
    else:
        lines.extend(
            [
                "## Surface observations",
                "",
                f"- Mean sequence similarity to neutral baseline: {_fmt(summary.get('mean_sequence_similarity'))}",
                f"- Exact-match fraction: {_fmt(summary.get('exact_match_fraction'))}",
                f"- First-token logprob availability: {_fmt(summary.get('logprob_available_fraction'))}",
                "",
                f"> {summary.get('warning', '')}",
            ]
        )

    lines.extend(
        [
            "",
            "## Artifact map",
            "",
            "- `receipt.json`: model, backend, capability, hashes, and environment receipt",
            "- `resolved_config.yaml`: sealed experiment configuration",
            "- `plan.json`: estimated run matrix before execution",
            "- `tokenization.jsonl`: raw glyph tokenization audit when locally available",
            "- `source_activations.npz` and `directions.npz`: source-stage tensors",
            "- `interventions.jsonl` or `surface_observations.jsonl`: condition-level records",
            "- `fingerprint_summary.jsonl`: held-out target, random-control, factor, and permutation diagnostics",
            "- `scalar_balance_summary.jsonl`: achieved intervention magnitude and output-displacement balance",
            "- `dose_response_summary.jsonl`: monotonicity across the positive strength grid",
            "- `sign_flip_summary.jsonl`: positive/negative local antisymmetry diagnostics",
            "- `cross_seed_fingerprint_summary.jsonl`: output fingerprint stability across source-direction seeds",
            "- `summary.json`: machine-readable pre-stage result",
            "",
        ]
    )
    report_path = run_dir / "report.md"
    atomic_write_text(report_path, "\n".join(lines))
    return report_path
