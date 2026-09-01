# Frozen manuscript claim table (v1)

[Japanese](CLAIM_TABLE.ja.md) | [Paper README](README.md)

Status: **frozen for manuscript draft v1** (supersedes v0 after the T20-C
result landed). Any change to the allowed wording, evidence denominator, or
exclusion requires a versioned update before the corresponding manuscript
sentence changes.

| Manuscript statement | Status and evidence | Required boundary |
|---|---|---|
| Atomic emoji retrieve lexically disjoint CLDR keyword aliases better than literal codepoints in at least three of four frozen core cells. | Supported: 4/4 core positive; partial-conjunction `p = 0.0027`. | Fixed T19-L text inputs, late-window readout, and top-1 endpoint only. |
| The alias result survives exact four-view token-count matching. | Supported: 9/9 cells pass unrestricted and matched components plus the `0.02` floor. | Token count is matched; token identity and tokenizer independence are not. |
| The relation extends beyond exact official short-name lookup. | Supported under the frozen endpoint: aliases are exact CLDR keywords whose ASCII-alphanumeric words are disjoint from canonical-name words. | A CLDR keyword is not a human-rated synonym or paraphrase and may have appeared in pretraining. |
| Emoji alias effects exceed symbol alias effects in the frozen panels. | Descriptive secondary: emoji-minus-symbol point estimates are positive in 9/9 cells for both components. | The emoji and symbol panels are not exchangeable in category, frequency, label quality, or token identity. |
| Official-name retrieval is broader than the emoji-only case. | Descriptive secondary: symbol canonical effects exceed symbol alias effects in 9/9 cells for both components. | This is a frozen-panel comparison, not a population estimate for Unicode symbols. |
| A rank-8 late `attn_out` or `mlp_out` component is jointly necessary and sufficient. | Not supported: neither primary block-24 site passed its joint criterion; no site passed both components. Post-hoc full-interchange ceilings at the primary sites are `0.0000`/`+0.0052`, so the registered floor exceeded attainable effects. | The registered decision is unchanged; the ceiling calibration is post-hoc and descriptive, and the negative is bounded to one Llama 3.2 3B cell, six sites, rank 8, and one endpoint. |
| Block-27 MLP is the causal mechanism. | Not supported: sufficiency adjusted `+0.0781`, necessity adjusted `-0.0156`; post-hoc composite ceiling `+0.2448` vs keyword-only `+0.0365` quantifies self-retrieval disruption. | The patch cannot be described as clean alias insertion. |
| An interchange-optimized rank-8 subspace at a late residual or component site is jointly necessary and sufficient. | Registered verdict: **uncalibratable at both primary sites** (sufficiency ceilings `+0.0234`/`+0.0254` below the registered `0.06` informativeness minimum); no secondary site passes. | The verdict is not evidence for the account; it records that the endpoint could not host the registered decision at these sites. One model, rank 8, readout-token interventions, four contexts. |
| The final-state keyword signal is not carried by the readout-token residual stream at blocks 21--24 and is reassembled from glyph-position context. | Supported descriptively by registered ceilings: full-swap necessity ceilings `4%`/`25%` of the attainable range at blocks 21/24 versus exact transfer (`100%`) at block 27; sufficiency ceilings `71%`/`76%`. | Ceilings are registered descriptive controls, not decision endpoints; the claim covers this cell, this retrieval endpoint, and readout-token single-position swaps only. |
| Optimized rank-8 subspaces memorize source items but find no shared carrier. | Supported descriptively: training InfoNCE falls to `0.52--1.26` at residual sites while held-out source validation stays at `0--1` item; fresh-bank adjusted sufficiency at most `+0.0046` (`p = 0.0085`), an order of magnitude below the floor. | Trained on 96 items; zero generalization is compatible with either item-private coding or insufficient training data. |
| Models visually perceive emoji or humanly understand their meaning. | Excluded. | Inputs are text-only Unicode scalars; no raster perception or behavioral understanding test was run. |
| The result identifies a universal emoji manifold, complete circuit, scale law, or model-population effect. | Excluded. | The nine cells are a fixed, confounded roster and the causal tests cover one model. |
| T19/T20 establish pretraining novelty or tokenizer independence. | Excluded. | Emoji surfaces may have appeared in earlier experiments or pretraining; only repository-text freshness for symbols, T19/T20-forward freshness for causal banks, and token-count matching are established. |

## Controlling sentence

> Raw atomic emoji retrieve lexically disjoint CLDR keyword aliases better
> than literal codepoints across nine frozen model/tokenizer cells after exact
> four-view token-count matching, while two preregistered causal experiments
> in one model fail to support any late readout-token subspace account — the
> closed-form rank-8 test fails its joint criterion at sites whose post-hoc
> ceilings are near zero, and the calibrated optimized-subspace follow-up is
> registered uncalibratable at its primary sites while its full-interchange
> ceilings localize the attainable signal to the final blocks and to
> glyph-position context.
