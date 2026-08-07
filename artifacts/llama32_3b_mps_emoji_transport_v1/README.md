# Llama 3.2 3B MPS emoji-transport v1 evidence

[日本語](README.ja.md) · [Protocol](../../docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1.md) · [Holdout status](../../docs/HOLDOUT_STATUS.md)

This directory is the public evidence root for the separately versioned E2
Transformers/MPS FP32 transport study. At static freeze it contains only this
bilingual orientation pair. A zero-model-forward preflight may then add
`preflight/tokenization_audit_v1.json` as the sole repository change before
execution.

If and only if all ten fixed cells complete and validation succeeds, the
no-overwrite publication builder adds compact `runs/` and complete `analysis/`
trees. The public bundle deliberately omits each local run's
`interventions.jsonl`, `source_activations.npz`, `directions.npz`, and
`target_baselines.npz`. Its root manifest records the SHA-256, byte count, and
row or array metadata for every omitted file and binds every published member.
The complete local run directories remain the authoritative replay evidence.

This study reuses 24 exploratory prestage targets. It does not use P2 or the
retired C1 v1 bank and cannot establish emoji semantics, tokenizer independence,
independent-target confirmation, causality, backend isolation, or model-scale
generality. An absent analysis tree means that no valid scientific result has
been published here.
