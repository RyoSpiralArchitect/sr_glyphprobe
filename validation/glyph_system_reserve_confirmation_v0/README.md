# Glyph-System Reserve Confirmation v0 compact evidence

[日本語](README.ja.md) · [Full result](../../docs/GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.md) · [Frozen protocol](../../docs/GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0.md)

This bundle contains the compact, Git-suitable evidence for T12's completed
one-shot reserve confirmation. Neither `H_ZWJ_FUSION` nor
`H_REGIONAL_DUAL` was confirmed.

Included:

- the frozen config, manifest, and design preflight;
- all nine tokenizer/artifact preflight receipts;
- all nine run receipts and shard indexes;
- the 432 item-contrast cell rows and complete joint primary result; and
- an independent recomputation of the stored medians, three 49,999-draw
  randomization tests, gates, intersection-union combination, and Holm family.

Omitted:

- raw FP32 activations and per-shard observations;
- model weights; and
- any intervention or generation output, because T12 made zero intervention
  and generation calls.

The omitted acquisition payload remains bound by the run and shard-ledger
hashes. Because raw activations are absent, this bundle independently validates
the stored inferential path but does not independently rebuild activation
contrasts or replicate the models.

Validate from the repository root:

```bash
python scripts/validate_glyph_system_reserve_confirmation_v0_result.py \
  validate-public-bundle \
  --bundle artifacts/glyph_system_reserve_confirmation_v0
```

The primary result SHA-256 is
`1dee4bd187c5816d809cec27c4972edb217442e7824ef172a7d5933557d491a6`.
No semantic, causal, behavioral-steering, tokenizer-independent, scale, or
model-general claim is authorized.
