# Llama 3.2 3B MPS emoji-transport v2 evidence

[日本語](README.ja.md) · [Protocol](../../docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.md) · [Holdout status](../../docs/HOLDOUT_STATUS.md)

Protocol ID: `glyphprobe-e2-llama32-3b-mps-emoji-transport-v2`

This directory is the separately versioned public evidence root for the v2
study. V1 remains an immutable zero-model-forward preflight failure. V2 changes
only the corrected tokenizer audit and every protocol, receipt, run, analysis,
log, and publication namespace required to keep the new attempt independent.

At static freeze this English/Japanese pair is the only payload here. A passed
zero-model-forward preflight adds
`preflight/tokenization_audit_v2.json`. Only a complete ten-process execution
and complete six-file analysis may add the final compact bundle.

The completed public bundle contains 15 copied files from each exact 19-file
local run. It deliberately omits `interventions.jsonl`,
`source_activations.npz`, `directions.npz`, and `target_baselines.npz`; the root
manifest records their SHA-256 hashes, byte counts, and JSONL or NPZ structural
inventories. The ten omitted intervention ledgers contain exactly 15,600 rows
in total. Launcher logs are also omitted because they contain local run paths.

The root manifest must bind this bilingual pair, both v2 publication adapters,
their frozen v1 base-script dependencies, the v2 analyzer, the v2 freeze
manifest, preflight, execution receipts, analysis, and every copied run member.
The builder and standalone validator reject absolute filesystem paths and
non-identical overwrites.

The 24 targets are reused exploratory prestage targets. The protected
`p2_confirmatory_targets_v1.jsonl` and `c1_causal_holdout_targets_v1.jsonl`
banks are declarations only: neither publication tool accepts, opens, reads,
hashes, tokenizes, or model-forwards their content.

This evidence can support only the bounded Transformers/MPS exploratory claim
defined by the protocol. It does not establish emoji semantics, tokenizer
independence, independent target confirmation, causal localization, backend
replication, or a model-scale effect.
