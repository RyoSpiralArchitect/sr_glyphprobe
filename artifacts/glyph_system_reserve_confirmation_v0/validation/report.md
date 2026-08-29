# T12 independent validation report

Status: **PASS with caveats**.

The validator did not import the T12 acquisition/analyzer module. It rehashed the frozen manifest, runtime preflight, nine run receipts, nine shard indexes, and joint analysis. It independently reconstructed 432 stored cell medians, reran all three 49,999-draw shared-item swap tests, and recomputed the practical-floor, model-heterogeneity, strict-prefix, intersection-union, and Holm decisions with zero mismatches.

Neither registered hypothesis was confirmed. The compact inputs omit raw FP32 activations, so the activation-to-item-contrast derivation was hash-bound but not independently recomputed. This is validation of the stored inferential path, not independent model replication.
