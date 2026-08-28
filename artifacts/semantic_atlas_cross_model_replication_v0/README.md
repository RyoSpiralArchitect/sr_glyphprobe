# Semantic atlas cross-model replication v0 evidence

[日本語](README.ja.md) · [Results](../../docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.md) · [Frozen protocol](../../docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.md)

This compact bundle records a completed, prospectively frozen nine-cell T10
replication. The registered cross-model primary was negative:
`cross_model_replication_not_established_under_frozen_rule`. Its statistical
partial conjunction passed (`p = 0.0001`), but only two of four core cells met
the practical rule; three were required.

The bundle contains:

- complete primary and secondary analysis outputs;
- compact per-model predictions and all cell metrics;
- run, summary, session, and nested shard-ledger bindings;
- a machine-readable independent validation result; and
- no raw activations or model weights.

The nine runs comprise 333 shards, 15,768 model forwards, and 126,144 FP32
readout vectors. The external raw archive contains 1,212,819,072 activation
bytes. The independent validator rehashed all 1,350 raw-ledger targets, checked
every activation array, and exactly reproduced the randomization, IUT, Holm,
and partial-conjunction results.

To revalidate the Git-resident evidence without model execution:

```bash
python scripts/validate_semantic_atlas_cross_model_replication_v0_result.py \
  --bundle artifacts/semantic_atlas_cross_model_replication_v0
```

Add `--raw-root path/to/glyphprobe-t10-runs-8673bc51` to include the external
raw archive. The command performs zero model forwards, interventions, or
generations.

Matching exact three-view token-count strata did not erase the observed
contrast, but this is not evidence of tokenizer independence. T10 does not
authorize semantic, causal, scale-law, tuning-effect, independent-replication,
architecture-general, model-general, or Phase I gate claims.
