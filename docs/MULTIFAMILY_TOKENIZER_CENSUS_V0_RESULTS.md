# Multifamily tokenizer census v0 results

[日本語](MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.ja.md) · [Frozen protocol](MULTIFAMILY_TOKENIZER_CENSUS_V0.md) · [Research roadmap](ROADMAP.md)

Analysis ID: `glyphprobe-multifamily-tokenizer-census-v0-posthoc-aggregate-v1`

## Result status

The three-node tokenizer-only census completed for all 14 frozen roster entries.
The deterministic post-hoc collector verified the node ledgers and published a
compact aggregate with `status: pass`.

This is descriptive control-design evidence. It is not an activation,
behavioral, confirmatory, semantic, or causal result, and it does not by itself
close a Phase I paper gate.

## Frozen scope and integrity

The census used the public v0 freeze at commit
`e3bea44a145d3c87f41fc5c60f90201b8cea2bdc`.

| Check | Result |
|---|---:|
| Nodes | `mac1`, `mac2`, `furnace` |
| Frozen roster entries completed | 14 / 14 |
| Fixed strings | 115 |
| Fixed tokenization contexts | 4 |
| Tokenization rows | 6,440 |
| Pairwise-control rows | 19,665 |
| Model-forward calls | 0 |
| Protected target files opened | 0 |

The collector reverified every node `SHA256SUMS`, receipt, summary, row count,
and shared config, manifest, and audit-script hash before aggregation. The Git
artifact retains path-scrubbed copies of the three source receipts and
summaries, a checksum ledger for each public node bundle, each original source
checksum ledger under the distinct name `SOURCE_SHA256SUMS`, exact raw-table
hashes, and row counts. The collection receipt binds the original unsanitized
source-receipt hashes while the public copies replace machine-local absolute
paths with a fixed marker. It intentionally omits the approximately 38 MiB raw
JSONL tables; hashes cannot reconstruct omitted data.

The compact bundle is bound by the
[`collection_receipt.json`](../artifacts/multifamily_tokenizer_census_v0/collection_receipt.json)
and top-level
[`SHA256SUMS`](../artifacts/multifamily_tokenizer_census_v0/SHA256SUMS).
The complete derived table is
[`aggregate.json`](../artifacts/multifamily_tokenizer_census_v0/aggregate.json).

## Seven exact output classes

The 14 roster entries collapsed to seven exact tokenization-output classes over
all 115 items and all four fixed contexts. Five classes reproduced exactly
across at least two nodes.

| Output class | Exact members on this fixed census | Raw mean | Raw median | Raw maximum |
|---|---|---:|---:|---:|
| 01 | Gemma 2 on furnace and mac2 | 1.296 | 1 | 7 |
| 02 | Gemma 3 4B/12B and Gemma 4 E4B | 1.435 | 1 | 7 |
| 03 | Mistral 7B Instruct v0.3 on all three nodes | 4.791 | 5 | 20 |
| 04 | GPT-2 on mac1 and mac2 | 3.374 | 3 | 14 |
| 05 | Llama 3.2 3B on mac1 and mac2 | 3.365 | 3 | 15 |
| 06 | OLMo 3 7B | 3.504 | 3 | 18 |
| 07 | Qwen 2.5 3B | 1.600 | 1 | 10 |

“Exact” here means identical recorded tokenization outputs on this fixed
115-item, four-context surface. It does not establish general tokenizer
identity, model equivalence, or equality outside the census.

## Cross-tokenizer fragmentation

Only six of 115 strings had the same raw token count across all seven output
classes: `control_brackets`, `control_colons`, `control_hashes`,
`control_lower_alpha`, `control_periods`, and `keycap_hash_base`.

The raw cross-class token-count range distribution was:

| Range | Item count |
|---:|---:|
| 0 | 6 |
| 1 | 6 |
| 2 | 10 |
| 3 | 3 |
| 4 | 78 |
| 5 | 6 |
| 7 | 5 |
| 13 | 1 |

The largest fragmentation occurred for `zwj_family`, whose raw span ranged
from 7 to 20 tokens. This is a tokenizer-structure observation, not evidence
that a model represents the family emoji more or less compositionally.

## Unicode composition

To avoid counting duplicated tokenizer artifacts as independent evidence, the
composition summary weights each of the seven exact output classes once.

| Construction | Relation | Observations | Histogram |
|---|---|---:|---|
| Keycap sequence | sequence minus base | 14 | `+1`: 4, `+4`: 10 |
| Skin-tone sequence | sequence minus base | 42 | `0`: 1, `+1`: 21, `+3`: 18, `+4`: 2 |
| Variation-selector sequence | sequence minus base | 35 | `0`: 7, `+1`: 28 |
| ZWJ sequence | sequence minus sum of fixed components | 56 | `0`: 8, `+1`: 21, `+2`: 21, `+3`: 3, `+6`: 3 |

These deltas describe token counts only. They do not measure semantic
composition or internal feature composition.

## Context sensitivity and round trips

The fixed glyph-plus-prompt suffix changed no span token count. It changed span
token IDs for six items in the Llama, OLMo, and Qwen classes and for none in
the other four classes. Leading-space sensitivity was much larger and differed
sharply by tokenizer class:

| Output class | Leading-space ID changes | Leading-space count changes | Glyph-prompt ID changes |
|---|---:|---:|---:|
| 01 Gemma 2 | 26 / 115 | 0 / 115 | 0 / 115 |
| 02 Gemma 3/4 | 25 / 115 | 1 / 115 | 0 / 115 |
| 03 Mistral v0.3 | 106 / 115 | 106 / 115 | 0 / 115 |
| 04 GPT-2 | 115 / 115 | 3 / 115 | 0 / 115 |
| 05 Llama 3.2 | 112 / 115 | 18 / 115 | 6 / 115 |
| 06 OLMo 3 | 112 / 115 | 21 / 115 | 6 / 115 |
| 07 Qwen 2.5 | 112 / 115 | 98 / 115 | 6 / 115 |

The marker-wrapper counts matched the recorded leading-space counts for every
class in this census. This is an observation on the fixed templates, not a
general wrapper-invariance claim.

Of 6,440 rows, 6,095 decoded exactly to the encoded text. All 345 non-exact
round trips were the 115 leading-space rows for each of the three Mistral v0.3
labels. The rows remain in the aggregate; the collector treats this as a
decoding-surface caveat rather than deleting or replacing the tokenizer.

## Focal control result: blue circle and blue square

For both `blue_circle` and `blue_square`, the fixed 115-item panel contained no
single candidate that simultaneously satisfied both conditions below across
all seven output classes in any of the three pairwise contexts (`raw`,
`leading_space`, or `glyph_prompt`):

1. equal item-span token count; and
2. at least one shared leading token, compared only within each tokenizer
   vocabulary.

The eight non-glyph ASCII controls did not provide even a universal equal-count
candidate for either focal item in those contexts. This means that one
universal control panel cannot be transported unchanged across the seven
observed tokenizer structures.

It does **not** mean that matched controls are unavailable. Many colored-shape
pairs match within GPT-2, Llama, OLMo, Mistral, or Qwen output classes. By
contrast, several Gemma colored shapes are distinct atomic tokens, so a shared
first-token requirement cannot be satisfied by a different glyph. The matching
rule must therefore be frozen per tokenizer output class rather than weakened
after outcomes are visible.

## Design consequence

The next activation protocol should define separate, prospective control sets
for each tokenizer output class. At minimum it should freeze:

- the exact input context and item-span rule;
- equal-count and prefix criteria that are feasible for that tokenizer;
- a declared fallback for atomic-token cases, such as token-count plus Unicode
  construction matching, reported as a distinct control family;
- the target bank, primary endpoint, hypothesis family, and multiplicity rule;
  and
- complete negative and failed-match reporting.

The census narrows the design space but does not select a winning model, layer,
emoji family, or intervention. Existing GPT-2 Milestone 2 results remain
unchanged; a future cross-tokenizer claim requires its own frozen controls and
outcome-independent target design.

## Revalidation

The compact published artifact can be checked without loading a tokenizer or
model:

```bash
python scripts/collect_multifamily_tokenizer_census_v0.py \
  --validate-output artifacts/multifamily_tokenizer_census_v0
```

The validator checks the complete compact-file roster, every recorded SHA-256,
the aggregate/receipt binding, and the collector-script hash. A passing receipt
is integrity evidence, not scientific confirmation.
