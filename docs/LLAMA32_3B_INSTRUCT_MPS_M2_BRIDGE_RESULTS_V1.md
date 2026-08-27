# Llama 3.2 3B Instruct M2 bridge results v1

[日本語](LLAMA32_3B_INSTRUCT_MPS_M2_BRIDGE_RESULTS_V1.ja.md) · [Protocol](LLAMA32_3B_INSTRUCT_MPS_M2_BRIDGE_V0.md) · [Analysis correction](LLAMA32_3B_INSTRUCT_MPS_M2_BRIDGE_ANALYSIS_CORRECTION_V1.md) · [Machine-readable receipt](../artifacts/milestone2/analyses/exploratory/llama32_3b_instruct_mps_m2_bridge_analysis_v1/analysis_receipt.json)

## Result

The prespecified exploratory bridge criterion was **not met**.

| Layer | Endpoint | Mean | Two-sided 95% bootstrap interval | Lower bound > 0.06 |
|---:|---|---:|:---:|:---:|
| 5 | Primary minus null A/B/C median | -0.02043 | [-0.04346, 0.00792] | No |
| 5 | Primary minus fully disjoint null A | -0.01571 | [-0.04172, 0.01497] | No |
| 11 | Primary minus null A/B/C median | 0.02285 | [0.00506, 0.04423] | No |
| 11 | Primary minus fully disjoint null A | 0.05532 | [0.03292, 0.07948] | No |

The primary rule required both layer-5 lower bounds to exceed the practical
threshold 0.06. Both layer-5 point estimates were slightly negative and their
intervals included zero. Layer 11 showed positive secondary estimates, but both
lower bounds remained below 0.06 and layer 11 was prospectively non-rescuing.
No p-value or confirmatory label is assigned.

## Interpretation

This is a clean negative transfer result for the tested cell. The GPT-2
Milestone 2 advantage did not reappear at normalized depth 0.20 in the pinned
Llama 3.2 3B Instruct Transformers/MPS BF16 setup after the strongest available
tokenizer-structural matching.

The layer-11 pattern is useful as a new hypothesis, not as a rescue: a
model-family or depth-dependent displacement may exist. It should not be
selected for causal work from this result alone. A future test must freeze that
hypothesis on new targets or distinguish model size, instruction tuning,
tokenizer, backend, and numerical precision with matched cells.

This result does not show that the original GPT-2 observation was only
tokenization, nor that glyph-conditioned geometry is absent. It shows that the
specified 3B transfer claim fails under its matched controls.

## Integrity and correction record

Four isolated model processes completed without resume. Analysis v0 then
failed at the first stored-config validation because it confused normalized
depth specifications `[0.2, 0.4]` with resolved layer indices `[5, 11]`. It had
not opened a run receipt, summary, or intervention ledger and produced no
analysis output.

Analysis correction v1 was committed publicly before outcomes were read. Its
score, bootstrap, endpoints, threshold, and decision rule are byte-for-byte or
constant-equivalent to v0; only the stored-config representation check changed.
The successful analysis verified public commit `af3e198`, all static hashes,
the exact four-process execution receipt, 20,000 bootstrap rows, and 48 target
effect rows.

P2 and retired C1 were not accessed. The 24 targets were previously used
prestage targets, so this remains exploratory and is neither an independent
confirmation nor a scale curve. The two unavoidable null-panel overlaps must
remain disclosed.
