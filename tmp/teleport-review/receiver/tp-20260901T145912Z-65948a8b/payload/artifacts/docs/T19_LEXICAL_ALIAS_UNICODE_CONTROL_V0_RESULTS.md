# T19 lexical alias × Unicode-symbol control: results

[日本語](T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0_RESULTS.ja.md) · [Frozen protocol](T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.md) · [Paper story](PAPER_STORY_T19_LEXICAL_NEIGHBORHOOD_V0.md)

Status: **T19-L registered primary positive; T19-C registered primary negative**.

## Result in one paragraph

Across all nine frozen model/tokenizer cells, raw atomic emoji retrieved a
lexically disjoint CLDR keyword alias better than a literal codepoint string in
both the unrestricted and exact four-view token-count-matched analyses. All
nine cells passed their model IUT and the `0.02` practical floors. The frozen
four-core partial-conjunction primary passed with 4/4 positive cells and
`p = 0.0027`. Non-emoji Unicode symbols showed smaller and heterogeneous alias
effects; the emoji-minus-symbol point estimate was positive in 9/9 cells in
both components, but this comparison was registered secondary. The conditional
causal follow-up then completed on 192 untouched emoji. All six zero-hook and
restoration controls were exact, yet neither primary block-24 site passed the
necessity–sufficiency intersection. T19 therefore supports a broad, token-count-
matched emoji-to-CLDR lexical correspondence, while rejecting the proposed
simple rank-8 late-component causal account.

## Frozen execution and evidence

- Execution freeze commit: `eec6f36261b2d2ee243c2404586eedc8e71adef1`
- Freeze SHA-256: `5dbbe0ef746cc3a002b8916de647a1c16a1e9f76a3f31fd4a0b53966f9c212fc`
- Selection SHA-256: `7a51d38effe67e74ff1264ae61c652e4192088063c3d31c874421f0b4dad8ee2`
- Observational analysis receipt: `1ebf8795c20463f2cff7b2ac5ff045aecaaeda2d8ddabc878822d6182b47e817`
- Independent observational validation: `afefacfeb75e8aeeb5bdfff34b4202f10f552087040177b81d2de5f405701b46`
- Causal go manifest: `1ac8d331f0ca2c40e9888857cd379d5c745f78a85c9c333fe33e7760cdba3df2`
- Causal source receipt: `f57f03bd97dcb9e2ebd8b8dda601a3351879e1a028abb471b94a2353678c2961`
- Causal evaluation receipt: `b519fd04ba307c61ec4d0b81b93b051669444f66e40d5c03b5a32463adfb0166`
- Causal analysis receipt: `cfd1983cdee843af6c00ea4b2a2c94eed5b34118631a6698c02c035d98855fa1`
- Independent causal validation: `dac9d28b74305b4db5536879961024470e4a4efbf29e527210b2662b93713355`

The observational run used 7,920 model forwards, 285,120 readout vectors, and
45 sealed shards. The causal run used 256 source forwards, 2,880 evaluation
forwards, and 8,064 intervention rows. Raw arrays remain in furnace scratch and
are not committed to Git.

## T19-L primary result

The statistic is the 24-context mean of
`top1(glyph → alias) − top1(glyph → codepoint)` on the 55 observational emoji.
`U` is unrestricted and `M` is exact token-count matched across glyph,
canonical label, alias, and codepoint literal.

| Frozen cell | U effect | M effect | Model IUT p | Positive |
|---|---:|---:|---:|:---:|
| Qwen 2.5 0.5B base | +0.0364 | +0.0702 | 0.00055 | yes |
| OLMo 2 1B base | +0.0652 | +0.0712 | 0.00135 | yes |
| Qwen 2.5 1.5B base | +0.0530 | +0.0631 | 0.00185 | yes |
| SmolLM2 1.7B base | +0.0606 | +0.0528 | 0.00005 | yes |
| Gemma 2 2B IT | +0.0886 | +0.0825 | 0.00005 | yes |
| Llama 3.2 3B base | +0.0856 | +0.1075 | 0.00135 | yes |
| Qwen 2.5 3B base | +0.0712 | +0.0833 | 0.00005 | yes |
| Qwen 2.5 7B base | +0.1818 | +0.1869 | 0.00005 | yes |
| Mistral 7B Instruct v0.3 | +0.2386 | +0.2577 | 0.00005 | yes |

The four frozen core cells—Llama 3.2 3B, Qwen 2.5 7B, OLMo 2 1B, and
Gemma 2 2B—were all positive. The third-smallest core IUT p-value was
`0.00135`; the registered `r = 3 of 4` Bonferroni partial-conjunction value was
therefore `2 × 0.00135 = 0.0027`. The gate required three cells and received
four.

The independent validator reconstructed all 36 kind × component randomization
tests from sealed prediction arrays, rehashed all 45 raw shards, checked every
summary/run binding, and reproduced the same gate decision.

## What changed relative to official short names

The alias endpoint was deliberately lexically disjoint from the official CLDR
short name. It still exceeded the codepoint endpoint in 9/9 model cells. This
rules out the narrow account that T18 only detected retrieval of the one exact
official label string.

It does not show synonym understanding. The aliases are exact CLDR keywords,
not human-rated paraphrases. They may have occurred beside the emoji or its
official name during training. Across models, the mean emoji alias-minus-
codepoint effect was `+0.0979` unrestricted and `+0.1084` matched, while the
mean canonical-name effects were larger, `+0.1440` and `+0.1718`. Official
names therefore remained the stronger key on average.

The depth profile was secondary. Averaged across models and contexts, the
unrestricted emoji alias contrast rose from `+0.0409` at the first block to
`+0.1152` at normalized depth `.875`, then ended at `+0.0922`. Individual
models did not share one onset or peak: some peaked at the first block, while
others peaked at `.75`, `.875`, or `1.0`.

## Non-emoji Unicode-symbol control

The 55 symbols were single non-emoji Unicode scalars absent from the frozen
repository text boundary. Their alias effects were heterogeneous:

- mean symbol alias-minus-codepoint was `+0.0236` unrestricted and `+0.0153`
  matched;
- Qwen 2.5 3B and 7B were negative in both symbol components;
- the emoji-minus-symbol point estimate was positive in all nine cells for
  both unrestricted and matched analysis;
- canonical-name retrieval exceeded alias retrieval for symbols in 9/9 cells
  in both components.

These are registered secondary results. They suggest that official-name
retrieval is not exclusive to emoji, while breadth toward a disjoint CLDR
keyword is much stronger for the frozen emoji panel. They do not establish an
emoji-specific semantic faculty, because label quality, training frequency,
token identity, symbol category, and visual familiarity remain uncontrolled.

## T19-C causal result

T19-C learned one rank-8 glyph–alias cross-covariance subspace per frozen site
from 128 source emoji, then intervened on 192 different emoji. Necessity was
the learned-subspace removal effect relative to a source-span random subspace.
Sufficiency was the learned glyph-to-codepoint patch relative to the analogous
random patch.

| Site | Primary | Necessity adjusted | p | Sufficiency adjusted | p | Engineering | IUT p |
|---|:---:|---:|---:|---:|---:|:---:|---:|
| `attn_out` block 21 | no | -0.00521 | 1.00000 | +0.00521 | 0.49983 | pass | 1.00000 |
| `mlp_out` block 21 | no | +0.00000 | 1.00000 | +0.00521 | 0.49760 | pass | 1.00000 |
| `attn_out` block 24 | yes | +0.00000 | 1.00000 | -0.00521 | 1.00000 | pass | 1.00000 |
| `mlp_out` block 24 | yes | +0.00521 | 0.49989 | +0.00000 | 0.74912 | pass | 0.74912 |
| `attn_out` block 27 | no | +0.00000 | 1.00000 | +0.01042 | 0.31511 | pass | 1.00000 |
| `mlp_out` block 27 | no | -0.01562 | 0.96895 | +0.07812 | 0.00009 | pass | 0.96895 |

All zero-hook and restoration final-state RMS values were exactly zero. The
primary negative result is therefore not an engineering-gate failure. At block
24, neither component came close to the `0.02` effect and lower-bound floors.

The secondary block-27 `mlp_out` sufficiency effect is a useful clue, not a
positive causal site. Its adjusted effect was `+0.07812`, one-sided
`p = 0.00009`, with a 95% item-bootstrap lower bound of `+0.03646`. Necessity
moved oppositely (`-0.01562`, `p = 0.96895`), so the frozen IUT failed. Moreover,
the sufficiency endpoint combined an alias top-1 rise from `0.0052` to `0.0208`
with a codepoint self-retrieval fall from `1.0000` to `0.9375`. It cannot be
described as clean alias insertion.

The independent causal validator rehashed source and evaluation arrays,
recomputed 12 sign-flip tests and 12 bootstrap intervals, checked all subspace
orthogonality and bindings, and reproduced six engineering passes and zero
positive primary sites.

## Interpretation

T19 narrows the explanatory space in two directions:

1. The raw emoji relation extends beyond one official short-name string to a
   lexically disjoint, source-auditable CLDR keyword in every frozen cell, even
   after exact token-count matching.
2. The relation is not explained by the registered simple mechanism: one
   source-learned rank-8 subspace at block-24 `attn_out` or `mlp_out` was neither
   jointly necessary nor sufficient on untouched items.

The combined result is consistent with distributed, redundant, nonlinear, or
item-private implementation. It does not distinguish those possibilities.
The negative intervention also applies only to one model, one rank, one
carrier/distance, two primary sites, and one final-hidden retrieval endpoint.

## Claim boundary

Authorized wording is limited to token-count-matched lexical correspondence in
the nine frozen model/tokenizer cells and a negative result for the registered
Llama 3.2 3B rank-8 component intervention. T19 does not establish rendered
glyph perception, human meaning, synonym understanding, pretraining novelty,
tokenizer independence, a universal emoji manifold, a unique or complete
circuit, model-population generality, instruction-tuning effects, or a scale
law.
