# T19 lexical alias × Unicode-symbol control

Status: **prospective execution freeze candidate; zero T19 model forwards and zero interventions**.

Japanese companion: [T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.ja.md](T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.ja.md)

## Research question

T18 showed that raw, repository-fresh composite emoji retrieve their official
English short names better than literal codepoint strings in the frozen late
window. T19 asks whether that relation extends beyond the official label:

> Does an atomic emoji retrieve a lexically disjoint CLDR keyword alias better
> than its literal `U+...` spelling, and how much of the same relation appears
> for atomic non-emoji Unicode symbols?

If the observational answer passes its single registered cross-model gate,
T19-C then asks whether a source-bank-learned rank-8 subspace at `attn_out` or
`mlp_out` makes a causal contribution on a third, untouched evaluation bank.

The experiment concerns text-model representations of Unicode scalar inputs.
It does not test rasterized glyph perception or human semantic understanding.

## What the alternative label is—and is not

For each item, `canonical_label` is the exact English CLDR 48.2 `tts` value.
`alias_label` is one exact English CLDR `default` keyword. After lowercasing
and extracting ASCII `[a-z0-9]+` words, the canonical and alias word sets must
both be nonempty and disjoint. Alias labels are globally unique across every
selected bank.

Examples include relations such as `birthday cake → dessert` and
`video game → controller`. These labels are source-auditable CLDR keywords.
They have **not** been human-rated as paraphrases, synonyms, natural names, or
equally specific descriptions. T19 therefore uses “keyword alias,” not
“human paraphrase,” in its claims.

## Three banks selected before any forward

| Bank | Items | Role | T19-L forwards at freeze |
|---|---:|---|---:|
| Observational emoji | 55 | registered primary | 0 |
| Observational non-emoji symbols | 55 | registered control and secondary | 0 |
| Causal source emoji | 128 | learn fixed subspaces only after admission | 0 |
| Causal evaluation emoji | 192 | held-out intervention endpoint | 0 |

All 430 codepoints and all 430 aliases are unique across the three banks. No
item may be moved, replaced, or excluded after freeze.

Atomic emoji are single-codepoint, fully qualified Emoji 17 entries introduced
no later than Emoji 13.1. Exact emoji surfaces may have appeared in earlier
repository experiments: T19 is prospective in its endpoint, alias assignment,
and bank split, not an exact-surface emoji holdout.

The symbol control is stricter within the repository boundary. A symbol must:

- consist of one Unicode scalar;
- have a Unicode general category beginning with `S`;
- have `Emoji=false` in Unicode Emoji 17 data;
- have an English CLDR annotation and a valid disjoint alias; and
- be absent as an exact scalar from every strict-UTF-8, no-NUL Git blob at
  commit `31b3bcc5f2a635306ebebeb8b66546135b8ca8b0`.

This is repository-relative surface freshness, not pretraining novelty.

## T19-L observational experiment

Each item has four text views:

1. raw `glyph`;
2. exact CLDR `canonical_label`;
3. fixed CLDR `alias_label`;
4. literal uppercase `codepoint_literal`.

The frozen T10/T18 harness supplies nine model/tokenizer cells, two suffix
carriers (`" a"` and `" |"`), distances `1, 2, 4, 8`, and nine normalized
depths. Batch size is one, no special token or chat template is added, and the
readout is the hidden state at the selected suffix token. The primary window
is fixed from T18 at normalized depths `.75`, `.875`, and `1.0`, producing 24
contexts per item.

For every view, representations are centered separately across items and
row-L2-normalized. The per-model statistic is the mean over the 24 contexts of:

```text
top1(glyph → alias) − top1(glyph → codepoint literal)
```

Only the 55 emoji enter the registered model and cross-model primary. The
non-emoji symbol contrast, canonical-name contrast, emoji-minus-symbol
difference, full depth curves, and other geometry metrics are registered
secondary outputs. This prevents a favorable control contrast from rescuing
the main emoji test.

## Tokenization-matched intersection

Every model must pass two components:

- **unrestricted:** all 55 observational emoji;
- **matched:** non-singleton strata with exactly equal token counts for glyph,
  canonical label, alias, and codepoint literal.

The alias correspondence is permuted within glyph kind for the unrestricted
component and within exact token-count strata for the matched component. The
codepoint and canonical correspondences remain fixed. Each component uses
19,999 randomization draws; the model p-value is their maximum. Both observed
contrasts must also be at least `0.02`.

Tokenizer-only preflight retained at least 63 items overall in every model,
with minima of 31 emoji and 32 symbols. All nine tokenizers exactly replayed
their complete frozen T10 reference sequence set. The matched component
controls token counts, not token identities or tokenizer construction.

## Cross-model decision and the causal gate

The sole cross-model primary reuses the four frozen core cells: Llama 3.2 3B
base, Qwen 2.5 7B base, OLMo 2 1B base, and Gemma 2 2B IT. The decision asks
whether at least three of four cells pass both the model IUT and both practical
floors. Its Bonferroni partial-conjunction p-value is twice the third-smallest
core-cell IUT p-value, capped at one.

T19-C remains closed unless that exact statistical-and-practical conjunction
passes. The other five model cells and every secondary endpoint cannot open the
gate.

## T19-C conditional causal experiment

The complete causal design is fixed before T19-L acquisition, but no causal
source or evaluation forward is permitted until admission is committed and
pushed.

- **Model:** frozen Llama 3.2 3B base cell only. This role was selected for
  pre-T19 hook compatibility and resource feasibility, not T19 outcomes.
- **Source bank:** 128 emoji, using glyph and alias at pipe carrier, distance 1.
- **Subspace:** rank 8, learned independently at each fixed component/depth by
  the left singular directions of centered, row-normalized glyph–alias
  cross-covariance.
- **Random control:** a deterministic rank-8 random subspace from the source
  span, orthogonal to the learned subspace.
- **Primary sites:** block 24 `attn_out` and block 24 `mlp_out`.
- **Secondary sites:** both components at blocks 21 and 27.
- **Evaluation bank:** 192 different emoji with no T19-L or source-bank forward.

At each site, necessity removes the learned coordinates from the glyph
component output. Sufficiency adds the same-item glyph-minus-codepoint learned
coordinates to the codepoint component output. Matched operations in the
random subspace estimate the control effect. A zero hook and a remove-then-
restore condition must reproduce the baseline final hidden state within the
frozen numerical tolerance.

The final-hidden endpoint is the same item-wise alias-minus-codepoint top-1
retrieval contrast. Each site uses a two-component intersection-union test:

```text
necessity: random-subspace result − learned-removal result
sufficiency: learned-patch result − random-subspace result
```

Both adjusted effects and both lower 95% item-bootstrap bounds must exceed
`0.02`. Both one-sided sign-flip tests must pass, with Holm correction across
the two primary sites, and the engineering controls must pass. A failure is
retained; no model, rank, depth, carrier, subset, or endpoint may be substituted.

## Outcome branches

- **T19-L positive, T19-C positive:** bounded evidence that atomic emoji map to
  a broader CLDR lexical neighborhood, with a causal contribution from at
  least one frozen late component/subspace cell.
- **T19-L positive, T19-C negative:** lexical alignment replicates, but the
  proposed low-rank late-component mechanism is unsupported.
- **Unrestricted positive, matched negative:** tokenization remains a
  sufficient alternative explanation; the causal gate stays closed.
- **Emoji and symbols both positive:** report a broader Unicode lexicalization
  account as secondary evidence, not emoji-specific semantics.
- **Emoji positive, symbols weak:** report emoji–symbol dissociation only from
  the registered secondary comparison and its uncertainty.
- **T19-L negative:** retain the complete atlas as a bounded failure to extend
  official-name retrieval to a lexically disjoint CLDR keyword.

## Execution gates

1. audit the source-bound selection and all three disjoint banks;
2. write zero-forward observational and causal design receipts;
3. run nine observational tokenizer preflights and one causal tokenizer
   preflight;
4. freeze config, selection, scripts, tests, bilingual protocol, receipts, and
   inherited T10/T18 bindings;
5. commit and push the freeze to `origin/main`;
6. recheck furnace availability immediately before model compute;
7. acquire and seal all nine T19-L cells, then analyze the registered gate;
8. if and only if the gate opens, commit and push a causal admission manifest;
9. acquire the source bank, seal its subspaces, then intervene on the untouched
   evaluation bank.

Raw activations remain in furnace scratch. Git receives only compact summaries,
analysis outputs, hashes, and bilingual reporting.

## Commands

```bash
python scripts/t19_lexical_alias_unicode_control_v0.py audit-selection
python scripts/t19_lexical_alias_unicode_control_v0.py audit-freeze --require-pushed
python scripts/t19_lexical_alias_unicode_control_v0.py run-role \
  --role MODEL_ROLE --model-path MODEL_SNAPSHOT --output-root RUN_ROOT
python scripts/t19_lexical_alias_unicode_control_v0.py summarize-role \
  --role MODEL_ROLE --output-root RUN_ROOT --summary-root SUMMARY_ROOT
python scripts/t19_lexical_alias_unicode_control_v0.py analyze-summaries \
  --summary-root SUMMARY_ROOT --output ANALYSIS_ROOT

# Conditional: only after a pushed go manifest exists.
python scripts/t19_lexical_alias_component_causal_v0.py run-source \
  --model-path LLAMA_SNAPSHOT --output-root SOURCE_ROOT
python scripts/t19_lexical_alias_component_causal_v0.py run-evaluation \
  --model-path LLAMA_SNAPSHOT --source-root SOURCE_ROOT --output-root EVAL_ROOT
python scripts/t19_lexical_alias_component_causal_v0.py analyze \
  --source-root SOURCE_ROOT --evaluation-root EVAL_ROOT --output CAUSAL_ANALYSIS_ROOT
```

The YAML contract, JSON manifests, and executable audits are authoritative if
prose differs.
