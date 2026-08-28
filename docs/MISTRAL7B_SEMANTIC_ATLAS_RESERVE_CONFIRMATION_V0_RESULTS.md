# Mistral 7B semantic atlas reserve confirmation v0 results

[日本語](MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0_RESULTS.ja.md) · [Frozen protocol](MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0.md) · [Evidence](../artifacts/mistral7b_semantic_atlas_reserve_confirmation_v0/README.md)

Status: **confirmed under the frozen rule**.

Outcome: `transport_robust_late_depth_glyph_name_alignment_confirmed`.

This closes the single T8 reserve question. It does not establish human emoji
meaning, a causal mechanism, tokenization independence, behavior, or model
generality.

## Prospective boundary and acquisition

The endpoint, full population, randomization seed, practical floor, and
positive/negative rule were committed at freeze commit `952b89d` before any
reserve forward. The freeze manifest SHA-256 is
`a678213ad79f3fced9c6cffe502b38e16b49a517cdf9d18ba75ef855a8efcc58`.

All 292 deterministic reserve items were then acquired exactly once under the
protocol's canonical batch-one route. The run made 1,752 model calls and stored
7,008 layer-31 FP32 vectors in ten complete shards. There were no partial
shards, interventions, generations, item replacements, or post-outcome cell
selections.

## Fixed primary result

The primary statistic was the minimum, over all two-carrier by four-distance
cells, of:

`glyph→official-name top-1 - glyph→U+codepoint top-1`.

The observed minimum was **`0.171233`**, compared with the frozen practical
floor `0.02`. The equal-cell mean contrast was `0.232021`. None of the 19,999
common-permutation null draws reached the observed minimum statistic, so the
prespecified p-value was **`(1 + 0) / 20,000 = 0.00005`**. Both components of
the positive rule passed.

Top-1 chance in this 292-item target pool is `1/292 = 0.003425`.

| Carrier | Distance | Glyph→name top-1 | Glyph→codepoint top-1 | Primary contrast | Glyph/name CKA | Glyph/codepoint CKA | CKA contrast |
|---|---:|---:|---:|---:|---:|---:|---:|
| `article_a` | 1 | 0.325342 | 0.003425 | 0.321918 | 0.402636 | 0.140630 | 0.262006 |
| `article_a` | 2 | 0.294521 | 0.010274 | 0.284247 | 0.303822 | 0.116169 | 0.187653 |
| `article_a` | 4 | 0.229452 | 0.000000 | 0.229452 | 0.234156 | 0.133755 | 0.100402 |
| `article_a` | 8 | 0.222603 | 0.000000 | 0.222603 | 0.136162 | 0.143844 | -0.007682 |
| `pipe` | 1 | 0.191781 | 0.003425 | 0.188356 | 0.292647 | 0.096938 | 0.195709 |
| `pipe` | 2 | 0.178082 | 0.006849 | **0.171233** | 0.245628 | 0.070903 | 0.174725 |
| `pipe` | 4 | 0.212329 | 0.003425 | 0.208904 | 0.263791 | 0.074354 | 0.189437 |
| `pipe` | 8 | 0.229452 | 0.000000 | 0.229452 | 0.235708 | 0.075553 | 0.160155 |

Every one of the eight primary retrieval contrasts exceeded the practical
floor. Official-name top-1 ranged from `0.178082` to `0.325342`, while
codepoint top-1 ranged from `0` to `0.010274`.

## Replication relation and secondary boundary

The discovery minimum contrast was `0.080760`, and its equal-cell mean was
`0.135392`. The untouched reserve therefore reproduced the direction and
complete-grid robustness without attenuation. The larger reserve values are
not evidence of a developmental trend or a second effect: the discovery and
reserve contain different deterministically selected items.

The primary result is specifically item-level retrieval. Centered linear CKA
was higher for glyph/name in seven of eight cells, but its contrast was
`-0.007682` at `article_a`, distance 8. CKA was secondary and cannot change the
decision. This heterogeneity is useful: the supported claim is correct-name
correspondence across transport cells, not uniform superiority of every global
geometry metric.

## Claim closed and next step

T8 may now be described as a prospectively confirmed, model-specific
late-depth glyph/name alignment result. `confirmatory_status` is true and
`t8_reserve_question_closed` is true.

The following remain false: semantic causality, causal localization,
tokenizer independence, behavioral relevance, and model generality. No complete
Phase I gate is declared closed by T8 alone.

The next research lane is claim-matched cross-model replication. Only after
that replication is sealed should the project return to exploratory unusual
glyph systems and representation shifts.
