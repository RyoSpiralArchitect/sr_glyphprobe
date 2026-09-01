# Frozen first-draft claim table

[Japanese](CLAIM_TABLE.ja.md) | [Paper README](README.md)

Status: **frozen for manuscript draft v0**. Any change to the allowed wording,
evidence denominator, or exclusion requires a versioned update before the
corresponding manuscript sentence changes.

| Manuscript statement | Status and evidence | Required boundary |
|---|---|---|
| Atomic emoji retrieve lexically disjoint CLDR keyword aliases better than literal codepoints in at least three of four frozen core cells. | Supported: 4/4 core positive; partial-conjunction `p = 0.0027`. | Fixed T19-L text inputs, late-window readout, and top-1 endpoint only. |
| The alias result survives exact four-view token-count matching. | Supported: 9/9 cells pass unrestricted and matched components plus the `0.02` floor. | Token count is matched; token identity and tokenizer independence are not. |
| The relation extends beyond exact official short-name lookup. | Supported under the frozen endpoint: aliases are exact CLDR keywords whose ASCII-alphanumeric words are disjoint from canonical-name words. | A CLDR keyword is not a human-rated synonym or paraphrase and may have appeared in pretraining. |
| Emoji alias effects exceed symbol alias effects in the frozen panels. | Descriptive secondary: emoji-minus-symbol point estimates are positive in 9/9 cells for both components. | The emoji and symbol panels are not exchangeable in category, frequency, label quality, or token identity. |
| Official-name retrieval is broader than the emoji-only case. | Descriptive secondary: symbol canonical effects exceed symbol alias effects in 9/9 cells for both components. | This is a frozen-panel comparison, not a population estimate for Unicode symbols. |
| A rank-8 late `attn_out` or `mlp_out` component is jointly necessary and sufficient. | Unsupported: neither primary block-24 site passed; no site passed both components. | Negative result is limited to one Llama 3.2 3B cell, six sites, rank 8, and one endpoint. |
| Block-27 MLP is the causal mechanism. | Unsupported: sufficiency adjusted `+0.0781`, but necessity adjusted `-0.0156`; secondary IUT `p = 0.96895`. | The patch partly lowers codepoint self-retrieval and cannot be described as clean alias insertion. |
| Models visually perceive emoji or humanly understand their meaning. | Excluded. | Inputs are text-only Unicode scalars; no raster perception or behavioral understanding test was run. |
| The result identifies a universal emoji manifold, complete circuit, scale law, or model-population effect. | Excluded. | The nine cells are a fixed, confounded roster and the causal test is one model. |
| T19 establishes pretraining novelty or tokenizer independence. | Excluded. | Emoji surfaces may have appeared in earlier experiments or pretraining; only repository-text freshness for symbols and token-count matching are established. |

## Controlling sentence

> Raw atomic emoji retrieve lexically disjoint CLDR keyword aliases better
> than literal codepoints across nine frozen model/tokenizer cells after exact
> four-view token-count matching, while a preregistered rank-8 late-component
> intervention in one model finds no primary site jointly necessary and
> sufficient for that readout.
