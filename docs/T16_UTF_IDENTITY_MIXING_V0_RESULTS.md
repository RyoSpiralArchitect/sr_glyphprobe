# T16 exact-UTF identity, family mixing, and sequence-length result

[日本語](T16_UTF_IDENTITY_MIXING_V0_RESULTS.ja.md) · [Frozen protocol](T16_UTF_IDENTITY_MIXING_V0.md) · [Closeout](../validation/t16_utf_identity_mixing_v0/closeout.json)

## Result in one paragraph

Exact repetition and construction-family diversity left separable hidden-state
geometry in both tested models. At `n=1`, clone, within-family mix, and
cross-family mix were the same byte string, the same prompt row, and exactly
zero on every displacement endpoint. For `n=2,4,8,16`, cross-family mixing had
a positive displacement excess over within-family mixing in all eight
model-by-depth cells; every stratified-bootstrap interval for
cross-minus-within excluded zero. The profile was depth-dependent rather than
monotone. Gemma's displacement expanded through the middle and late stack,
then contracted sharply at the final block. Mistral retained a large
cross-family excess at the late and final blocks even after exact-clone growth
fell. This is an exploratory, tokenizer-conditional geometry result—not a
tokenizer-independent Unicode or semantic decomposition.

## Primary descriptive summaries

Each principal-unit value averages `n=2,4,8,16`; intervals use 20,000
bootstrap replicates stratified by the six Unicode construction families.

| Model | Depth | Block | Clone growth | Within-family extra | Cross-family extra | Cross minus within, 95% interval |
|---|---:|---:|---:|---:|---:|:---:|
| Gemma 2 2B IT | 0.25 | 5 | 0.036007 | 0.012968 | 0.031494 | 0.012005 [0.010682, 0.015212] |
| Gemma 2 2B IT | 0.50 | 12 | 0.116261 | 0.072632 | 0.122892 | 0.046260 [0.041255, 0.054119] |
| Gemma 2 2B IT | 0.75 | 18 | 0.130213 | 0.090632 | 0.129563 | 0.041057 [0.031462, 0.047299] |
| Gemma 2 2B IT | 1.00 | 25 | 0.019195 | 0.016435 | 0.023182 | 0.007419 [0.005687, 0.008589] |
| Mistral 7B Instruct v0.3 | 0.25 | 7 | 0.048883 | 0.021029 | 0.045706 | 0.022963 [0.018296, 0.025429] |
| Mistral 7B Instruct v0.3 | 0.50 | 15 | 0.084063 | 0.044994 | 0.084425 | 0.035101 [0.031685, 0.042528] |
| Mistral 7B Instruct v0.3 | 0.75 | 23 | 0.049622 | 0.045185 | 0.094574 | 0.047833 [0.036481, 0.054128] |
| Mistral 7B Instruct v0.3 | 1.00 | 31 | 0.030167 | 0.031511 | 0.083574 | 0.037238 [0.030508, 0.048114] |

The consistent sign of cross-minus-within is the main descriptive pattern.
The magnitudes should not be compared as if model hidden spaces were on a
shared absolute scale.

## Dependence on sequence length

The table reports the median cross-minus-within displacement at each `n`.
Every `n=1` value is exactly zero by construction and is omitted.

| Model | Depth | n=2 | n=4 | n=8 | n=16 |
|---|---:|---:|---:|---:|---:|
| Gemma 2 2B IT | 0.25 | 0.008515 | 0.012286 | 0.011385 | 0.017612 |
| Gemma 2 2B IT | 0.50 | 0.023081 | 0.041424 | 0.056152 | 0.067126 |
| Gemma 2 2B IT | 0.75 | 0.025857 | 0.036361 | 0.036586 | 0.055121 |
| Gemma 2 2B IT | 1.00 | 0.004342 | 0.004519 | 0.009375 | 0.012308 |
| Mistral 7B Instruct v0.3 | 0.25 | 0.013342 | 0.021231 | 0.024394 | 0.029137 |
| Mistral 7B Instruct v0.3 | 0.50 | 0.021747 | 0.029631 | 0.048098 | 0.050151 |
| Mistral 7B Instruct v0.3 | 0.75 | 0.022110 | 0.039887 | 0.063671 | 0.059660 |
| Mistral 7B Instruct v0.3 | 1.00 | 0.017050 | 0.027637 | 0.049026 | 0.053152 |

The excess generally accumulated with sequence length, but it was not
strictly monotone in every cell. This is why the registered primary summary
averages the four nontrivial sequence lengths rather than selecting the
largest `n`.

## What exact identity controlled

The panel contains four exact strings from each of six construction families:
atomic scalars, VS16 presentation sequences, modifier sequences, ZWJ
sequences, regional-indicator flags, and keycaps. `clone_exact_utf` repeats one
anchor byte-for-byte. The within- and cross-family conditions start with the
same exact anchor, and all three conditions map to the same captured prompt at
`n=1`. Across both models, the complete run contains 2,880 factorial records
mapped to 2,496 unique prompts, with zero generation calls.

## Tokenization boundary

Exact UTF identity inside the clone arm does not match tokenizer paths across
mixed arms. Per depth, the exact-token-count subset contained 256
within-family and 52 cross-family pairs for Gemma, and 152 within-family and 20
cross-family pairs for Mistral. The cross-family subset is sparse—only four
pairs at some sequence lengths and none at `n=16`. Its nonzero distances are a
descriptive sensitivity check, not an independent test and not a rescue of the
main result.

The result therefore supports a tokenizer-conditional decomposition of exact
repetition, within-construction diversity, and cross-construction diversity.
It does not prove that Unicode construction family itself is causally encoded,
that the effect survives token-identity matching, or that the geometry is
semantic.

## Evidence

- [Compact analysis](../validation/t16_utf_identity_mixing_v0/results/analysis.json), SHA-256 `4e388d505a39d91e8c8bfc5c69127878e5484ab904e39d5a5d9ba5b66f658b1b`
- [Tokenizer preflight](../validation/t16_utf_identity_mixing_v0/tokenizer_preflight.json)
- [Closeout](../validation/t16_utf_identity_mixing_v0/closeout.json), including both model receipt hashes and the exact `n=1` invariant

Raw activation arrays remain in the recorded furnace scratch root and were not
copied into Git.
