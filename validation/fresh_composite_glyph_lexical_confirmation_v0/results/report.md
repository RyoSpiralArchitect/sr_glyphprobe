# Fresh composite-glyph lexical confirmation v0 result

Outcome: `fresh_exact_surfaces_confirmed_in_at_least_three_of_four_core_cells`.

| Model cell | Unrestricted estimate | Matched estimate | Unrestricted p | Matched p | IUT p | Holm p | Practical |
|---|---:|---:|---:|---:|---:|---:|---|
| `qwen25_0p5b_base_bf16` | 0.044922 | 0.045070 | 0.0000500 | 0.0001000 | 0.0001000 | 0.0004500 | true |
| `olmo2_1b_base_bf16` | 0.046947 | 0.046161 | 0.0000500 | 0.0000500 | 0.0000500 | 0.0004500 | true |
| `qwen25_1p5b_base_bf16` | 0.111256 | 0.119424 | 0.0000500 | 0.0000500 | 0.0000500 | 0.0004500 | true |
| `smollm2_1p7b_base_bf16` | 0.017940 | 0.025511 | 0.0000500 | 0.0000500 | 0.0000500 | 0.0004500 | false |
| `gemma2_2b_it_bf16` | 0.032118 | 0.030267 | 0.0000500 | 0.0000500 | 0.0000500 | 0.0004500 | true |
| `llama32_3b_base_bf16` | 0.087529 | 0.099401 | 0.0000500 | 0.0000500 | 0.0000500 | 0.0004500 | true |
| `qwen25_3b_base_bf16` | 0.122251 | 0.133049 | 0.0000500 | 0.0000500 | 0.0000500 | 0.0004500 | true |
| `qwen25_7b_base_bf16` | 0.178530 | 0.192587 | 0.0000500 | 0.0000500 | 0.0000500 | 0.0004500 | true |
| `mistral7b_instruct_v03_bf16` | 0.231409 | 0.251458 | 0.0000500 | 0.0000500 | 0.0000500 | 0.0004500 | true |

Core partial-conjunction p: `0.0001000`; practical-only core passes: `4/4`; joint model-IUT-and-practical core passes: `4/4`.

Freshness is relative to the frozen tracked repository tree and exact UTF-8 surfaces. It is not a pretraining or semantic-concept holdout. The result concerns text-codepoint sequence geometry, not rendered-glyph perception, causality, or behavior.
