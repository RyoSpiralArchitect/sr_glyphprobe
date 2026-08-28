# Multifamily dense CUDA carrier-distance v0 result

Outcome pattern: `no_dense_model_distance_attenuation`.

| Model | d=1 p | attenuation p | IUT p | Holm p | Reject |
|---|---:|---:|---:|---:|---|
| `gemma2_2b_it` | 0.765300000 | 0.770900000 | 0.770900000 | 1.000000000 | false |
| `gemma3_4b_it` | 0.753000000 | 0.845150000 | 0.845150000 | 1.000000000 | false |
| `mistral7b_instruct_v03` | 0.000050000 | 0.469750000 | 0.469750000 | 1.000000000 | false |
| `gemma3_12b_it` | 0.825800000 | 0.975750000 | 0.975750000 | 1.000000000 | false |

The decision requires both distance-1 recurrence and the fixed positive log-distance contrast. This post-T5 exploratory CUDA family does not establish scale effects, base/instruct equivalence, backend parity, semantics, causality, confirmation, monotonicity, or duration.
