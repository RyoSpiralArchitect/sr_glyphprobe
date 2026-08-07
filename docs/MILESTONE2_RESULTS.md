# Milestone 2 results: token-count and prefix-panel controls

[日本語](MILESTONE2_RESULTS.ja.md) · [Protocol](MILESTONE2_PROTOCOL.md) · [Roadmap](ROADMAP.md) · [Artifact manifest](../artifacts/MILESTONE2_MANIFEST.json)

## Outcome first

The frozen v1 analysis produced a mixed, layer-specific result.

| Source-wrapper arm | Layer | Mean adjusted target effect | 95% v1 bootstrap CI | Holm-adjusted one-sided p | Frozen v1 status |
|---|---:|---:|:---:|---:|---|
| primary source | 2 | +0.208363 | [0.137463, 0.276893] | 0.00143999 | robust to the prespecified matched controls |
| primary source | 4 | -0.0329465 | [-0.0761085, 0.0110094] | 0.999500 | unresolved |
| independent source | 2 | +0.187507 | [0.125489, 0.247659] | 0.00393996 | robust to the prespecified matched controls |
| independent source | 4 | -0.086379 | [-0.159246, -0.016917] | 0.999430 | unresolved |

The minimally meaningful positive excess was frozen at `delta = 0.06`. A layer received the robust status only when the v1 interval lower bound exceeded `0.06` and the one-sided sign-flip p-value remained below `0.05` after Holm correction across layers 2 and 4. Layer 4 is unresolved in both arms. In particular, the entirely negative independent-source interval does not satisfy either the positive-robustness rule or the practical-equivalence rule; it is not evidence of absence.

The independent-source arm changes the source-wrapper bank but reuses the same 48 P2 targets, model, tokenizer, backend, layers, and endpoint. It is a source-construction robustness check, not an independent target, backend, or model replication.

The outcome-blind public freeze is commit `2be9f5be6181b24ff8ebf96ab42445d80dd936a9`. The P2 model forwards began only after that commit had been pushed.

## What was compared

For each of 48 frozen P2 targets in six prespecified groups, the analysis measured cross-target condition identifiability: mean cosine similarity to the same-condition leave-one-target-group-out prototype minus mean similarity to the other conditions. The three direction seeds were averaged inside each target. The target-level endpoint was

```text
D[t] = colored-shape score[t] - median(null A[t], null B[t], null C[t]).
```

The three ten-symbol null panels match the colored-shape panel on the prespecified GPT-2 token count and panel-level 9:1 prefix structure. They do **not** match token identity. Exact token-ID matching would decode to the same input bytes and would not provide a distinct glyph input. Panel C includes one declared conservative semantic-near control, the nonreference red square `🟥`, because only 26 eligible non-colored symbols were available for 27 disjoint dominant-prefix slots. The other 29 null-panel entries are non-colored.

Accordingly, the supported label is **robust to the prespecified token-count and token-prefix matched panels**. It is not a tokenization-free glyph effect.

## Exploratory matched-panel comparison

Before the one-shot P2 analysis, the original 24-target exploratory matrix was compared with null panels A/B/C. At the original 96-dimensional CountSketch, the median paired cell difference between the colored-shape score and the median matched-null score was `+0.047427`; 25 of 36 layer–seed–strength cells were positive and 11 were nonpositive.

This is descriptive only. The 36 cells share targets and repeated design structure and are not independent observations. The difference is not a proportion, so it does not estimate a “percent of the original result explained by tokenization.”

| CountSketch dimension | Median paired difference |
|---:|---:|
| 96 | +0.047427 |
| 48 | +0.040200 |
| 32 | +0.028907 |
| 24 | +0.048591 |

Dimensions 48, 32, and 24 are exact same-seed algebraic folds of the stored 96-dimensional sketches. They probe dimensional compression under one fixed sketch seed; they are **not** CountSketch-seed sensitivity or independent reruns.

## Frozen v1 inference and its limitations

The v1 analyzer correctly enforces the frozen model cell, P2 target IDs and groups, layer/strength/seed family, complete run receipts, disjoint condition IDs, target-level sampling unit, and Holm family. Two qualifications remain important.

First, the analyzer assigns the four scientific roles from CLI position: primary first, followed by null A/B/C. Its internal checks do not, by themselves, cryptographically establish that each directory came from the intended frozen panel and source config. A separate [input-binding audit](../artifacts/milestone2/input_binding_audit.json) resolves that gap against the frozen preregistration manifest and audit. It passed the exact config-role, panel-role, source-family, target-bank, input-path, and input-hash checks for all 14 published runs: the 12 core exploratory, P2, and independent-source arms plus the two diagnostics.

Second, v1 constructs the leave-one-target-group-out prototypes once from the observed P2 bank, computes one effect per target, and bootstraps those fixed target effects. It does not rebuild the prototypes inside every bootstrap replicate. The resulting v1 inference is conditional on the observed prototypes and does not propagate their resampling dependence. Its p-values and statuses remain the frozen confirmatory output; the separate post-hoc analysis below does not retroactively reclassify them.

## Post-hoc dependence-aware sensitivity

A separate post-hoc analysis used the same stratified target draws jointly across the primary panel, null panels A/B/C, both layers, and all three fixed seeds, rebuilding every leave-one-target-group-out prototype inside each replicate.

| Source-wrapper arm | Layer | Point estimate | Rebuilt-prototype 95% interval | Fixed-prototype interval on the same draws |
|---|---:|---:|:---:|:---:|
| primary source | 2 | +0.208363 | [0.099930, 0.295380] | [0.137463, 0.276893] |
| primary source | 4 | -0.0329465 | [-0.099995, 0.041902] | [-0.076108, 0.011009] |
| independent source | 2 | +0.187507 | [0.104210, 0.271322] | [0.125489, 0.247659] |
| independent source | 4 | -0.086379 | [-0.185084, 0.007648] | [-0.159246, -0.016917] |

This analysis was specified after P2 outcomes were available. Its intervals are descriptive sensitivity intervals: no p-value, Holm adjustment, practical-equivalence decision, or confirmatory status is assigned. It conditions on the fixed panels, fixed seeds, fixed group labels, and empirical P2 target bank, and it does not estimate panel-selection or seed-selection uncertainty. The exact values and method are in the [primary-source sensitivity receipt](../artifacts/milestone2/analyses/posthoc_dependence/p2/m2_dependence_sensitivity_receipt.json) and [independent-source sensitivity receipt](../artifacts/milestone2/analyses/posthoc_dependence/independent_source/m2_dependence_sensitivity_receipt.json). The frozen v1 statuses above are not overwritten.

## Completed secondary diagnostics

The suffix-matched middle-token-shift and prefix-homogeneous colored-shape panels were each run across the complete 14,208-row exploratory grid. Both runs recorded zero errors, zero-hook activation/logit RMS of 0, and readiness of 11 / 11.

| Diagnostic panel | Rows | Errors | Zero-hook RMS | Readiness | Headline `emoji_fingerprint_advantage` |
|---|---:|---:|---:|---:|---:|
| suffix-matched middle-token shift | 14,208 | 0 | 0 | 11 / 11 | +0.751225 |
| prefix-homogeneous colored shapes | 14,208 | 0 | 0 | 11 / 11 | +0.601038 |

Those headline values are random-adjusted run summaries. They are not the raw separation scores used in the paired comparisons below and must not be equated with them.

| CountSketch dimension | Standard minus suffix raw separation, median | Standard minus prefix-homogeneous raw separation, median |
|---:|---:|---:|
| 96 | +0.002624 | +0.022096 |
| 48 | +0.009473 | +0.023254 |
| 32 | +0.004026 | +0.011040 |
| 24 | +0.009700 | +0.025387 |

At 96 dimensions, 20 of 36 standard-minus-suffix cells and 25 of 36 standard-minus-prefix cells were positive. These are post-hoc descriptive diagnostics, not confirmatory tests or equivalence analyses. The 48-, 32-, and 24-dimensional values are same-seed algebraic folds, not sketch-seed sensitivity or independent reruns.

One runtime irregularity is retained for provenance. The first foreground matched-null A process was externally interrupted after 798 ledger rows during severe machine load; median latency was about 309 ms, compared with a 10.73 ms baseline. A sealed resume completed the exact 14,208-row grid with no duplicate or missing rows, zero errors, and zero-hook activation/logit RMS of 0; later median latency returned to about 12.43 ms. This is operational provenance, not model evidence or a universal speed claim. P2, independent-source, and diagnostic runs completed normally.

Milestone 2 did not pass C1 v1 to a model or use it in outcome analysis. The
bank is now retired after a separately recorded research-context exposure; see
[Holdout status](HOLDOUT_STATUS.md). It must not be described or reused as an
untouched bank.

## Claim boundary and next decision

Milestone 2 supports a narrow statement: in this pinned GPT-2 FP32 MLX `resid_post` cell, layer 2 exceeded the three prespecified token-count and prefix-panel controls under both source-wrapper banks according to the frozen v1 rule; layer 4 did not. The result does not establish glyph semantics, a mechanism, a circuit, a causal path, a tokenization-free effect, or generalization beyond this cell.

Operational Milestone 2 is complete. Layer 2 is now eligible for the design of
a new frozen targeted causal protocol; layer 4 remains unresolved and is not a
candidate. C1 v1 cannot serve that experiment. A new versioned bank must be
prepared outside the exposed research context and kept untouched until the
candidate, intervention site and operation, endpoint, controls, and
multiplicity family are frozen publicly. This eligibility authorizes protocol
design, not a causal claim.

Phase I still ends with an English paper and a Japanese public summary. The paper must report the mixed layer result, both v1 and post-hoc uncertainty boundaries, the completed descriptive diagnostics, and the remaining causal and replication gates. Its final confirmatory wording, and any replication used to support that wording, must prospectively address analyzer role binding and prototype-resampling dependence.

## Evidence map

- Compact Milestone 2 inventory and omission record: [artifacts/MILESTONE2_MANIFEST.json](../artifacts/MILESTONE2_MANIFEST.json)
- Outcome-blind public freeze: commit `2be9f5be6181b24ff8ebf96ab42445d80dd936a9`; P2 model forwards began only after it was pushed
- Frozen protocol: [MILESTONE2_PROTOCOL.md](MILESTONE2_PROTOCOL.md)
- Primary-source v1 receipt: [m2_confirmatory_receipt.json](../artifacts/milestone2/analyses/confirmatory/p2/m2_confirmatory_receipt.json)
- Independent-source v1 receipt: [m2_confirmatory_receipt.json](../artifacts/milestone2/analyses/confirmatory/independent_source/m2_confirmatory_receipt.json)
- Exploratory 96-dimensional paired comparison: [matched_panel_comparison_dim96.json](../artifacts/milestone2/analyses/exploratory/matched_panel_comparison_dim96.json)
- Input-binding audit: [input_binding_audit.json](../artifacts/milestone2/input_binding_audit.json)
- Post-hoc primary-source sensitivity: [receipt](../artifacts/milestone2/analyses/posthoc_dependence/p2/m2_dependence_sensitivity_receipt.json)
- Post-hoc independent-source sensitivity: [receipt](../artifacts/milestone2/analyses/posthoc_dependence/independent_source/m2_dependence_sensitivity_receipt.json)
- Suffix diagnostic, 96-dimensional paired comparison: [suffix_vs_standard_dim96.json](../artifacts/milestone2/analyses/diagnostics/suffix_vs_standard_dim96.json)
- Prefix-homogeneous diagnostic, 96-dimensional paired comparison: [prefix_homogeneous_vs_standard_dim96.json](../artifacts/milestone2/analyses/diagnostics/prefix_homogeneous_vs_standard_dim96.json)
