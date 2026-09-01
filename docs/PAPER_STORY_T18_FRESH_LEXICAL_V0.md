# T18 paper story: fresh-surface lexical binding

[日本語](PAPER_STORY_T18_FRESH_LEXICAL_V0.ja.md) · [T18 results](FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0_RESULTS.md) · [T18 protocol](FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0.md) · [T17 precursor](PAPER_STORY_T17_GLYPH_NAME_V0.md)

Status: **candidate workshop-paper spine, not a frozen manuscript claim table**.

## Candidate title

> **From Codepoints to Names: Fresh-Surface Lexical Binding of Composite Emoji in Language Models**

## One-sentence contribution

Across a prospectively frozen set of 192 multi-codepoint emoji surfaces absent
from the prior study repository, raw Unicode sequences retrieved standardized
English short names better than literal codepoint strings in all four core
model/tokenizer cells after exact token-count matching, while depth, global
geometry, and item identity remained model-specific.

That sentence is the paper. It is narrow enough to defend and rich enough to
matter.

## Why this is a cleaner return to the glyph question

The project began by asking whether emoji and other glyph-like inputs leave
distinct internal fingerprints. T16 showed that Unicode construction, order,
and sequence length can move hidden states strongly, so any semantic reading
needs hard structural controls. T17 then found a broad raw-emoji-to-name
retrieval relation, but on items already opened in T9/T10. T18 supplies the
missing prospective gate:

1. select exact raw surfaces before tokenizer measurement;
2. exclude the complete prior T11 identity set;
3. freeze the late window from T17 before observing T18 activations;
4. require unrestricted and exact token-count-matched effects together;
5. require the same three of four core cells to pass statistics and the
   practical floor;
6. independently recompute the exposure audit and all 18 randomization tests.

The result is not “models see emoji pictures.” It is a controlled statement
about how a text model lexicalizes a standardized multi-codepoint sequence.

## Three empirical layers

### 1. Confirmed aggregate relation

All four core cells passed. The partial-conjunction result was `p = 0.0001`,
and 8/9 registered cells met the full statistical-plus-practical rule. This is
the confirmatory center of the paper.

### 2. Multilingual and structural boundaries

The Japanese-minus-codepoint point estimate was positive in all nine models,
including the Japanese-specific token-count strata, but it was a secondary
family. This weakens an English-label-only story without proving
language-independent meaning. Exact token-count matching removes one strong
alternative explanation while leaving token identity and sequence structure
open.

### 3. Aggregate universality, model-private implementation

Paired item margins favored names in all nine models, yet matched CKA did so in
only 3/9. Only 8/192 items were positive in every core model, and pairwise core
item-effect correlations were only `0.0245`–`0.2035`. The interesting result is
therefore not one universal emoji manifold. It is a recurrent aggregate
lexical relation built from different internal item rosters and trajectories.

## Position relative to prior work

The closest strands answer different questions:

- [emoji2vec](https://aclanthology.org/W16-6208/) learns emoji embeddings from
  textual descriptions; T18 diagnoses an already-trained model and compares a
  raw sequence with fixed label and codepoint views.
- [ELCo](https://aclanthology.org/2024.lrec-main.1381/) studies phrase-level
  composition of multiple emojis in behavioral tasks; T18 studies one
  standardized multi-codepoint grapheme cluster at a time inside hidden-state
  geometry.
- [What Do Tokens Know About Their Characters and How Do They Know It?](https://aclanthology.org/2022.naacl-main.179/)
  probes orthographic contents of subword tokens; T18 asks about item-specific
  correspondence between a raw Unicode sequence and its standardized lexical
  label, with a literal encoding control.
- [Assessing Emoji Use in Modern Text Processing Tools](https://aclanthology.org/2021.acl-long.110/)
  maps broad NLP handling failures; T18 isolates one representation-level
  relation under a frozen multi-model design.

The population labels come from pinned [Unicode Emoji 17 data](https://www.unicode.org/Public/17.0.0/emoji/emoji-test.txt)
and [CLDR JSON 48.2.0](https://github.com/unicode-org/cldr-json/tree/48.2.0).

## Suggested paper structure

1. **Question and threat model.** Raw Unicode surface, lexical label, and
   literal encoding are separable; rendered perception is out of scope.
2. **Prospective population.** Explain exact-surface repository freshness and
   why it is not a pretraining holdout.
3. **Frozen experiment.** Nine cells, equal-system endpoint, late window,
   token-count strata, IUT, partial conjunction, and practical floor.
4. **Primary result.** Lead with the four core cells and the independent
   recomputation, then show all nine cells.
5. **How the relation is implemented.** Depth heterogeneity, CKA dissociation,
   multilingual secondary, and sparse item overlap.
6. **Boundaries.** T16 Unicode construction controls, tokenizer limits, shared
   training lineage, and no visual or causal claim.
7. **Next test.** Official label versus paraphrase and non-emoji named-symbol
   controls, followed by a separately frozen causal localization.

T15 behavior and steering results can motivate the broader program, but they
should not compete with T18 for the main claim. T16 belongs primarily in the
threat-model or appendix role: it explains why the narrower lexical reading is
necessary.

## Figure plan

- **Figure 1:** design schematic—raw emoji, English/Japanese short name, and
  codepoint literal; exact-surface exposure boundary.
- **Figure 2:** nine-model late-window unrestricted and matched contrasts with
  the `0.02` floor.
- **Figure 3:** full depth trajectories, emphasizing heterogeneous peaks rather
  than a shared transition.
- **Figure 4:** paired-margin versus CKA sign and core item-overlap matrix.
- **Appendix:** system-specific profiles, Japanese-specific matching, Qwen
  descriptive sequence, tokenizer coverage, and all receipts.

## Claim table for later manuscript freeze

| Candidate claim | Current status | Boundary |
|---|---|---|
| Fresh raw emoji retrieve English short names better than codepoint literals in at least 3/4 frozen core cells | supported | registered late-window model cells only |
| Result survives exact token-count matching | supported | not token-identity or tokenizer independence |
| Japanese labels show the same directional pattern | descriptive 9/9 | no registered Japanese inference |
| One shared late-layer transition exists | unsupported | peaks and onsets differ |
| One globally aligned emoji-name manifold exists | unsupported | matched CKA positive in 3/9 |
| The same emoji items drive every model | unsupported | only 8/192 positive in all core cells |
| Models visually perceive or humanly understand emoji | unauthorized | text-codepoint input only |
| Effect grows with parameter count | unauthorized | Qwen profile is confounded and descriptive |
| A causal lexical circuit has been identified | not tested | requires a new freeze and untouched bank |

## Best next experiment

The next experiment should not merely add more emoji. Use a crossed lexical
control:

```text
raw emoji
  × official short name
  × preselected paraphrase or common alias
  × Japanese label
  × literal codepoint string
  × named non-emoji Unicode symbol control
```

Freeze a small primary contrast that distinguishes official-label lookup from
broader lexical neighborhood retrieval. Only after that gate should the study
compare late `attn_out` and `mlp_out` removal/addition/restoration on a new
untouched evaluation bank. Consensus and model-private items may be strata,
but the outcome of T18 must not be used to cherry-pick the sole causal site.

## Writing boundary

Use “exact-surface-fresh,” “repository-relative,” “lexical binding,” and
“item-specific retrieval.” Avoid “unseen to the model,” “visual glyph
recognition,” “semantic understanding,” “universal,” “scale law,” and
“independent nine-model replication.”
