# Manuscript claims and evidence (v2)

[Japanese](CLAIM_TABLE.ja.md) | [Paper README](README.md)

Status: **specified for manuscript revision v2**. This editorial revision
retains every T19/T20 result and decision while distinguishing measured swap
effects from hypotheses about their source. Any change to the allowed wording, evidence denominator, or
exclusion requires a versioned update before the corresponding manuscript
sentence changes.

| Manuscript statement | Status and evidence | Required boundary |
|---|---|---|
| Atomic emoji retrieve word-disjoint CLDR keywords better than literal codepoints in at least three of four prespecified core configurations. | Supported: 4/4 core positive; partial-conjunction `p = 0.0027`. | Fixed T19-L text inputs, late-window readout, and top-1 endpoint only. |
| The keyword result survives exact four-view token-count matching. | Supported: 9/9 configurations pass unrestricted and matched components plus the `0.02` floor. | Token count is matched; token identity and tokenizer independence are not. |
| The relation extends beyond exact official short-name lookup. | Supported under the prespecified endpoint: the exact CLDR keywords share no ASCII-alphanumeric word with the official names. | A CLDR keyword is not a human-rated synonym or paraphrase and may have appeared in pretraining. |
| Emoji keyword effects exceed symbol keyword effects in the prespecified panels. | Descriptive secondary: emoji-minus-symbol point estimates are positive in 9/9 configurations for both components. | The emoji and symbol panels are not exchangeable in category, frequency, label quality, or token identity. |
| Official-name retrieval extends to non-emoji symbols. | Descriptive secondary: symbol official-name effects exceed symbol keyword effects in 9/9 configurations for both components. | This comparison covers the specified panels and supplies no population estimate for Unicode symbols. |
| A rank-8 late `attn_out` or `mlp_out` component is jointly necessary and sufficient. | Not supported: neither primary block-24 site passed its joint criterion; no site passed both components. Post-hoc full-state sufficiency effects at the primary sites are `0.0000`/`+0.0052`, below the registered floor. | The registered decision is unchanged; the calibration is post-hoc and descriptive, and the negative is bounded to one Llama 3.2 3B configuration, six sites, rank 8, and one endpoint. |
| Block-27 MLP is the causal mechanism. | Not supported: sufficiency adjusted `+0.0781`, necessity adjusted `-0.0156`; post-hoc composite ceiling `+0.2448` vs keyword-only `+0.0365` quantifies self-retrieval disruption. | The patch cannot be described as clean alias insertion. |
| An interchange-optimized rank-8 subspace at a late residual or component site is jointly necessary and sufficient. | Registered verdict: **uncalibratable at both primary sites** (sufficiency ceilings `+0.0234`/`+0.0254` below the registered `0.06` informativeness minimum); no secondary site passes. | The verdict records a failed calibration requirement and leaves the account unresolved. One model, rank 8, readout-token interventions, four contexts. |
| Full readout-token swaps have asymmetric effects at blocks 21 and 24 and reproduce both baselines at block 27. | Supported descriptively by registered controls: necessity effects are `4%`/`25%` of the baseline glyph--codepoint gap at blocks 21/24 versus exact transfer (`100%`) at block 27; sufficiency effects are `71%`/`76%`. | Preserved retrieval motivates a hypothesis of recovery from unchanged glyph-position context. The interventions do not identify that pathway, exclude all ranks, or prove that a full swap upper-bounds every subspace intervention. |
| The tested optimized rank-8 subspaces fit source items and generalize weakly to held-out items. | Supported descriptively: training InfoNCE falls to `0.52--1.26` at residual sites while held-out source validation stays at `0--1` item; fresh-set adjusted sufficiency at most `+0.0046` (`p = 0.0085`, uncorrected component test), below one quarter of the `0.02` floor. | Trained on 96 items; weak generalization is compatible with item-specific coding, limited training data, or optimization limits. It does not establish that no shared subspace exists. |
| Models visually perceive emoji or humanly understand their meaning. | Excluded. | Inputs are text-only Unicode scalars; no raster perception or behavioral understanding test was run. |
| The result identifies a universal emoji manifold, complete circuit, scale law, or model-population effect. | Excluded. | The nine cells are a fixed, confounded roster and the causal tests cover one model. |
| T19/T20 establish pretraining novelty or tokenizer independence. | Excluded. | Emoji surfaces may have appeared in earlier experiments or pretraining; only repository-text freshness for symbols, T19/T20-forward freshness for causal banks, and token-count matching are established. |

## Controlling sentence

> Raw atomic emoji retrieve word-disjoint CLDR keywords better than literal
> codepoints across nine prespecified model--tokenizer configurations after
> exact four-view token-count matching. Neither causal experiment supports
> the tested rank-8 readout-token account. The optimized-subspace follow-up
> is uncalibratable at its primary sites under the registered rule. Its
> full-state swaps reveal a depth-dependent asymmetry and motivate direct
> tests of recovery from glyph-position context.
