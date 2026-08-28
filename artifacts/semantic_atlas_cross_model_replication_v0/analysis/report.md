# Semantic atlas cross-model replication v0 result

Outcome: `cross_model_replication_not_established`.

| Model cell | Unrestricted p | Matched p | IUT p | Holm p | Practical | Bounded cell |
|---|---:|---:|---:|---:|---|---|
| `llama32_3b_base_bf16` | 0.0000500 | 0.0000500 | 0.0000500 | 0.0004500 | true | true |
| `qwen25_7b_base_bf16` | 0.0000500 | 0.0000500 | 0.0000500 | 0.0004500 | true | true |
| `olmo2_1b_base_bf16` | 0.0000500 | 0.0000500 | 0.0000500 | 0.0004500 | false | false |
| `gemma2_2b_it_bf16` | 0.0000500 | 0.0000500 | 0.0000500 | 0.0004500 | false | false |
| `qwen25_0p5b_base_bf16` | 0.0000500 | 0.0000500 | 0.0000500 | 0.0004500 | false | false |
| `qwen25_1p5b_base_bf16` | 0.0000500 | 0.0000500 | 0.0000500 | 0.0004500 | false | false |
| `qwen25_3b_base_bf16` | 0.0000500 | 0.0000500 | 0.0000500 | 0.0004500 | false | false |
| `smollm2_1p7b_base_bf16` | 0.0000500 | 0.0001000 | 0.0001000 | 0.0004500 | false | false |
| `mistral7b_instruct_v03_bf16` | 0.0000500 | 0.0000500 | 0.0000500 | 0.0004500 | true | true |

Core partial-conjunction p: `0.0001000`; practical core passes: `2/4`.

This result concerns frozen model/tokenizer cells and official Unicode item-name retrieval. It does not establish emoji semantics, causality, independence, a scale law, or model generality.
