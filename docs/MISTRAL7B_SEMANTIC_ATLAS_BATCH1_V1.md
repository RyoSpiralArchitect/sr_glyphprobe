# Mistral 7B semantic atlas batch-one v1

[日本語](MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1.ja.md) · [Original acquisition](MISTRAL7B_SEMANTIC_ATLAS_V0.md) · [Analysis plan](MISTRAL7B_SEMANTIC_ATLAS_V0_ANALYSIS.md)

Status: **prospectively frozen replacement acquisition; zero batch-one v1
forwards**.

The original batch-64 atlas completed all 28 shards, but its independently
frozen batch-one recapture validation failed 18/18 cases. The worst case had
minimum vector cosine `0.998244270`, relative RMS error `0.078983818`, and
maximum absolute error `2.5`, against thresholds `0.999999`, `0.001`, and
`0.125`. The discrepancy is consistent with meaningful BF16 batch-shape
numeric sensitivity at later residual states. It cannot be repaired by
loosening thresholds after seeing the result.

V1 therefore repeats exactly the same 892 acquired items, three views, two
carriers, four fused causal distances, nine layers, FP32 export, source order,
and 28 item shards at batch size one. It changes no scientific input and makes
5,352 model calls. The batch-64 data and failed receipt are retained as a
numerical-sensitivity artifact; they are not silently replaced.

The same fixed acquisition indices `[0, 445, 891]`, all views, and both
carriers are then independently recaptured again at batch one under the same
18-case thresholds. All 18 must pass before v1 may serve as the canonical input
to the already frozen descriptive analyzer.

The 292-item reserve remains at zero forwards. V1 is an engineering repair,
not a new semantic endpoint, independent confirmation, or paper-gate result.
