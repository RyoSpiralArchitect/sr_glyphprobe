# Multifamily carrier-distance v0 result

Outcome pattern: `no_model_distance_attenuation`.

| Model | d=1 p | attenuation p | IUT p | Holm p | Reject |
|---|---:|---:|---:|---:|---|
| `gemma2_2b_4bit` | 0.443100000 | 0.573250000 | 0.573250000 | 1.000000000 | false |
| `llama32_3b_bf16` | 0.000050000 | 0.188000000 | 0.188000000 | 0.564000000 | false |
| `olmo3_7b_bf16` | 0.000050000 | 0.997700000 | 0.997700000 | 1.000000000 | false |

The primary decision requires both distance-1 recurrence and the fixed positive log-distance contrast. It does not establish monotonic decay, disappearance, semantics, causality, tokenizer equivalence, backend equivalence, confirmation, or a Phase I gate decision.
