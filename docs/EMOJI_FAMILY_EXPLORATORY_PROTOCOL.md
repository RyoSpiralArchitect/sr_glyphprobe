# E1 exploratory protocol: token-isomorphic emoji-family screen

[日本語](EMOJI_FAMILY_EXPLORATORY_PROTOCOL.ja.md) · [Research roadmap](ROADMAP.md) · [Scientific contract](SCIENTIFIC_CONTRACT.md)

Protocol ID: `glyphprobe-e1-token-isomorphic-emoji-families-v1`

## Status and question

E1 is a bounded exploratory side track. It asks whether slot-specific output-fingerprint separation recurs when only the middle token of a three-token emoji changes across five fixed Unicode blocks.

The scientific choices below are fixed before E1 activation outcomes are inspected. The executable freeze is complete only when a public commit binds this document pair to the panel file, run configuration, tokenizer audit, analysis code, environment and model receipts, and a checksum manifest. Until then, the execution status is `freeze_pending`.

E1 is not a Milestone 2 confirmation, a C1 causal experiment, or an independent-backend replication. It creates no P2, P3, C1, robustness, significance, or paper-gate status.

## Frozen emoji blocks

Each inclusive range contains ten code points. Family names are registry labels for reporting, not semantic annotations to be tested.

| Family ID | Inclusive Unicode block | Pinned GPT-2 first-two-token prefix | Slots |
|---|---|---:|---:|
| `sky` | `U+1F311`–`U+1F31A` | `[8582, 234]` | 10 |
| `food` | `U+1F351`–`U+1F35A` | `[8582, 235]` | 10 |
| `animals` | `U+1F411`–`U+1F41A` | `[8582, 238]` | 10 |
| `transport` | `U+1F691`–`U+1F69A` | `[8582, 248]` | 10 |
| `social` | `U+1F911`–`U+1F91A` | `[8582, 97]` | 10 |

No family, code point, slot order, or display label may be added, removed, reordered, or renamed after the executable freeze. All five families remain in the public result, including null, negative, or heterogeneous outcomes.

## Token-isomorphism contract

For family \(k\) and matched slot \(j\), the raw glyph tokenization must have the form

\[
\operatorname{tokens}(k,j) = [8582,\ m_k,\ r_j].
\]

The first token is `8582` for every glyph. The family-specific middle token \(m_k\) is `234`, `235`, `238`, `248`, or `97` as listed above. In ascending code-point order, the matched-slot third tokens \(r_j\) are `239` through `248`; each \(r_j\) must be identical across all five families. Thus all glyphs have exactly three raw tokens; across a matched slot, only the middle token changes with family.

Before any model forward pass, the tokenizer audit must record every code point, UTF-8 byte sequence, decoded round trip, raw token ID sequence, and source-wrapper token-position profile. The audit must fail closed if any glyph is not three tokens, any family prefix differs from the table, any matched third-token ID differs across families, or any wrapper introduces a family-dependent token count, intervention position, or outside token.

This is an exact structural match for one pinned tokenizer, not a tokenization-free comparison. Family identity and the middle token ID are perfectly confounded by design, while matched-slot transfer can be explained by the deliberately shared first and third token IDs. E1 therefore measures recurrence under a controlled middle-token substitution; it cannot identify an emoji meaning or a tokenizer-independent glyph property.

## Fixed data roles

- Targets: only the first 24 rows of [`prestage_targets.jsonl`](../data/targets/prestage_targets.jsonl), comprising four targets in each of six existing groups: `continuation`, `factual`, `reasoning`, `procedural`, `classification`, and `planning`.
- Source contexts: all 16 rows of [`source_wrappers.jsonl`](../data/wrappers/source_wrappers.jsonl).
- Target use: these 24 targets have already served exploratory work. They are reused only for E1 exploration and must not be described as untouched or confirmatory.
- Forbidden inputs: neither the P2 target bank nor the sealed C1 target bank may be read, tokenized, scored, sampled, or used for model, tokenizer, panel, endpoint, or analysis selection.

The executable freeze must bind the ordered target IDs, group labels, ordered wrapper IDs, exact file hashes, and maximum-row limits. Appending rows to a source file must not silently enlarge E1.

## Fixed model and intervention cell

E1 uses one pinned model/runtime family:

- model: `openai-community/gpt2`;
- revision: `607a30d783dfa663caf39e06633721c8d4cfcd7e`;
- backend and arithmetic: MLX, FP32;
- execution tokenization: `backend.add_special_tokens: false`;
- capture site: `resid_post`;
- source anchor, capture position, and intervention position: `last_nonpad`;
- attention capture: disabled (`capture.return_attentions: false`);
- input surface: emoji input `{emoji}\n{prompt}`, neutral baseline `{prompt}`, and
  no system prompt;
- layers: 2 and 4 only; layer 2 is the primary exploratory row and layer 4 is
  the prespecified secondary negative comparator;
- intervention strength: 0.05 only;
- source-direction seeds: 101, 211, and 307;
- random controls: two random directions per layer;
- integrity/control switches: zero hook enabled; neutral-direction and sign-flip
  arms disabled.

The existing source-wrapper subsampling rule and fingerprint construction are retained and must be hash-bound in the executable configuration. Direction seeds are repeated estimates within a target, not independent samples. Random directions are control rows, not additional target observations. The zero hook is an integrity check, not an E1 endpoint. No layer, strength, seed, tokenizer, fingerprint setting, or family may be selected or rescued after outcomes are visible.

## Exploratory endpoints

Let \(f_{k,j,t,s}\) be the unit-normalized output fingerprint for family \(k\), slot \(j\), target \(t\), and source-direction seed \(s\). Let \(c(t)\) be the prespecified target group. Every prototype is leave-one-target-group-out (LOTO):

\[
q_{k,j,-c,s}=\operatorname{unit\_mean}\{f_{k,j,u,s}:c(u)\ne c\}.
\]

For evaluation family \(f\) and prototype family \(g\), define the matched-slot score as the matched cosine minus the mean cosine to the nine mismatched slots:

\[
M_{f\leftarrow g,t,s}=\frac{1}{10}\sum_j\left[\cos(f_{f,j,t,s},q_{g,j,-c(t),s})-\frac{1}{9}\sum_{\ell\ne j}\cos(f_{f,j,t,s},q_{g,\ell,-c(t),s})\right].
\]

The diagonal \(M_{f\leftarrow f}\) is within-family separation. Every off-diagonal \(M_{f\leftarrow g}\), \(g\ne f\), is cross-family shared-suffix transfer: fingerprints from row \(f\) are evaluated against LOTO prototypes from row \(g\). Average the three seed values inside each target,

\[
\bar M_{f\leftarrow g,t}=\frac{1}{3}\sum_s M_{f\leftarrow g,t,s},
\]

then compute the row-specific excess over transfer,

\[
R_{f,t}=\bar M_{f\leftarrow f,t}-\operatorname{median}_{g\ne f}\bar M_{f\leftarrow g,t},
\]

and the family-equal global value at each target,

\[
R_{\mathrm{global},t}=\frac{1}{5}\sum_f R_{f,t}.
\]

For each target-level quantity \(Z_t\), the primary descriptive aggregate is the equal-target mean \(\bar Z=24^{-1}\sum_t Z_t\). E1 reports the complete 5-by-5 mean \(M\) matrix, all five mean \(R_f\) rows, and the mean \(R_{\mathrm{global}}\). No favorable family, direction, or off-diagonal pair is promoted to a primary result. The layer-2 mean \(R_{\mathrm{global}}\) is the primary exploratory summary; layer 4 is the prespecified secondary negative comparator. Target medians and target-group distributions may be reported only as secondary descriptions. The two random directions per layer are controls and never inflate the target count.

## Descriptive uncertainty

Uncertainty uses 20,000 stratified target-bootstrap replicates. Each replicate samples four targets with replacement inside each of the six fixed groups. The same sampled target indices are reused across families, layers, endpoints, and ordered family pairs so that comparisons remain paired.

All data-dependent LOTO prototypes are rebuilt inside every replicate from that replicate's resampled non-held-out groups. Reusing full-data prototypes inside the bootstrap is prohibited. Seeds remain nested within targets and are not resampled as independent units.

Within each replicate, recompute the complete \(M\) matrix, all \(R_f\), and the family-equal \(R_{\mathrm{global}}\), then take the equal-target mean. For each reported cell, publish the observed target-level mean and the 2.5th and 97.5th percentiles of the 20,000 bootstrap replicate means. Target medians and target-group distributions may accompany them as secondary descriptions, together with the full family-pair matrix. The bootstrap seed and implementation hash must be fixed in the executable manifest before the first E1 model forward.

These intervals are descriptive. E1 computes no p-values, multiplicity-adjusted decisions, equivalence tests, or status labels such as `robust`, `confirmed`, or `significant`.

## Stopping and publication rule

The frozen grid is run once. Runtime failures may be resumed from sealed rows, but outcomes cannot trigger extra families, layers, strengths, seeds, endpoints, or replacement targets. Any unavoidable deviation is versioned, disclosed, and analyzed separately; it does not overwrite the frozen E1 result.

After the executable freeze, publish:

1. the complete five-family panel and tokenizer audit;
2. configuration, provenance, validation, and integrity receipts;
3. the complete \(M\) matrix, all \(R_f\) rows, and \(R_{\mathrm{global}}\);
4. null, negative, heterogeneous, and failed cells;
5. the 20,000-replicate descriptive bootstrap output and analysis code;
6. any interruption, resume, exclusion, or deviation record.

## Claim boundary and next decision

The strongest permitted positive wording is: **exploratory matched-slot fingerprint recurrence under a fixed middle-token family substitution in one pinned GPT-2 MLX FP32 intervention cell**.

E1 does not establish semantic categories, family-independent emoji representations, causal localization, tokenizer independence, cross-model generality, backend replication, or behavioral meaning. Its colored-shape factor diagnostics are inapplicable: E1 assigns no color, shape, family-factor, slot-factor, or interaction status.

E1 does not update the Milestone 2 classification, choose a C1 intervention site, unseal C1, or satisfy a Phase I paper gate. If E1 motivates a narrower hypothesis, confirmation requires a new public protocol and a new untouched target bank that is neither P2 nor C1. The confirmatory prototype, endpoint, hypothesis family, multiplicity rule, and decision boundary must then be frozen before that new bank is accessed.
