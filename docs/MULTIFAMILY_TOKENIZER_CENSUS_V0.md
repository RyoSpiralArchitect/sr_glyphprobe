# Multifamily tokenizer census v0

[日本語](MULTIFAMILY_TOKENIZER_CENSUS_V0.ja.md) · [Research roadmap](ROADMAP.md) · [Scientific contract](SCIENTIFIC_CONTRACT.md)

Protocol ID: `glyphprobe-multifamily-tokenizer-census-v0`

## Status and purpose

This is a frozen, tokenizer-only structural census prepared before any live
output for this 115-item census is inspected. Its executable freeze becomes
active in the first public commit that contains this document pair, the fixed
panel and configuration, the audit script and tests, and the checksum manifest.

The census asks which token-count and token-prefix structures survive when the
existing GPT-2-shaped emoji controls are transported to several tokenizer
families, and how Unicode composition changes those structures. It is a control
design step, not an activation or behavioral experiment.

## Fixed questions

The census records four descriptive questions without a positive-result gate:

1. **Cross-tokenizer fragmentation:** how much does each fixed string's raw
   token count vary across the frozen tokenizer roster?
2. **Prefix-control availability:** which item pairs have equal token count and
   a shared first one or two tokens within each tokenizer, under the raw,
   leading-space, and glyph-plus-prompt surfaces?
3. **Composition increment:** for skin-tone, variation-selector, keycap, and
   ZWJ sequences, how does sequence token count differ from the fixed base or
   the sum of fixed component token counts?
4. **Wrapper sensitivity:** does the token span overlapping the item change
   when the same item is raw, preceded by a space, placed in a marker wrapper,
   or followed by the fixed prompt `probe`?

These questions can expose control candidates or confounds. They cannot
identify meaning, representation, mechanism, or causal effect.

## Fixed panel

The ordered panel has 115 unique strings:

- 50 single-code-point items from the five existing E1 blocks: sky, food,
  animals, transport, and social;
- 10 existing colored circle/square items, including `blue_circle` and
  `blue_square`;
- 8 hand/skin-tone base and sequence items;
- 16 fixed ZWJ component items and 8 fixed ZWJ sequences;
- 4 regional-indicator flags;
- 7 text/emoji presentation pairs involving U+FE0F;
- 4 keycap base/sequence items; and
- 8 non-glyph ASCII controls.

The exact order and relationships are bound by
[`multifamily_tokenizer_sequences_v0.yaml`](../data/emoji_panels/multifamily_tokenizer_sequences_v0.yaml),
the six pre-existing panel files named by the configuration, and the freeze
manifest. No item may be added, removed, renamed, reordered, or replaced after
live output is visible. Any revised panel requires a new protocol version.

Family names are reporting strata. They are not semantic labels tested by this
census. A Unicode display that appears visually unified may contain multiple
code points, a variation selector, a zero-width joiner, or regional indicators;
the audit records the exact code points and UTF-8 bytes.

## Fixed tokenization surfaces

Every tokenizer uses `local_files_only=true`, `use_fast=true`,
`trust_remote_code=false`, and `add_special_tokens=false`. Each item is audited
under four exact templates:

| Context ID | Template |
|---|---|
| `raw` | `{item}` |
| `leading_space` | ` {item}` |
| `marker_wrapper` | `Marker: {item} ->` |
| `glyph_prompt` | `{item}\nprobe` |

Fast-tokenizer offset mappings define the item-overlapping token span. For each
row the audit retains token IDs, token pieces, offsets, span positions, decoded
text, round-trip status, code points, and UTF-8 bytes. Token IDs are compared
only within one tokenizer vocabulary.

## Frozen availability-based roster

The roster was selected from tokenizer artifacts already present on the three
nodes, before this census output was inspected. Quantized and unquantized model
artifacts may share tokenizer assets; the audit hashes the actual local files
instead of assuming identity from a model name.

| Node | Frozen tokenizer labels |
|---|---|
| `mac1` | `mac1_llama32_3b`, `mac1_mistral7b_instruct_v03`, `mac1_gpt2`, `mac1_gemma4_e4b_it`, `mac1_olmo3_7b` |
| `mac2` | `mac2_llama32_3b_bf16`, `mac2_mistral7b_instruct_v03_4bit`, `mac2_gemma2_2b_4bit`, `mac2_qwen25_3b`, `mac2_gpt2` |
| `furnace` | `furnace_gemma2_2b_it`, `furnace_gemma3_4b_it`, `furnace_gemma3_12b_it`, `furnace_mistral7b_instruct_v03` |

Every label must appear in its node receipt. A load or compatibility failure is
retained as a failure row and does not authorize a replacement tokenizer after
results are visible. Missing Llama 3 8B and Gemma 2 base snapshots on the
furnace were excluded before freeze because no complete local tokenizer
snapshot was present; this protocol does not download them.

## Fixed descriptive outputs

For tokenizer (m), item (i), and context (c), let
(n_{m,i,c}) be the number of tokens whose offsets overlap the item. The census
publishes:

- every tokenization row;
- per-family raw token-count histograms;
- each item's minimum, maximum, and range of raw token count across successful
  roster entries;
- base deltas (n_{m,i,raw}-n_{m,b(i),raw});
- component-sum gaps
  (n_{m,i,raw}-\sum_{j\in components(i)}n_{m,j,raw}); and
- all unordered item pairs, including equal-count, shared-prefix, and exact
  within-tokenizer sequence indicators for the fixed pairwise contexts.

All 6,555 unordered pairs are retained. Candidate filtering happens only after
the complete table exists and cannot delete unfavorable pairs. Equal token
count, a shared prefix, or an exact token sequence is a structural observation,
not evidence of semantic equivalence.

## Execution and failure rule

The command takes one `--tokenizer LABEL=LOCAL_PATH` argument for every label in
the selected node roster. The provided label set must match that roster exactly.
Outputs are staged in a sibling hidden directory and published by one rename.
The output directory contains:

- `tokenizations.jsonl`;
- `pairwise_controls.jsonl`;
- `summary.json`;
- `receipt.json`; and
- `SHA256SUMS`.

The receipt records tokenizer/config/script assets, package/runtime identity,
all success and failure rows, output counts and hashes, and explicit zero values
for model-forward calls and protected-target access. A tokenizer failure does
not erase rows from other tokenizer labels. If every tokenizer fails, the
artifact bundle is still published as a failed receipt and the command returns
a nonzero status. Any partial roster failure is also surfaced with a nonzero
status while retaining the complete-with-failures bundle.

## Protected inputs and claim boundary

The script does not read target cases, source wrappers, model weights,
activations, logits, or behaviors. In particular, it must not open, sample,
tokenize, or otherwise inspect either the used P2 confirmatory bank or the
retired C1 bank.

The strongest permitted statement is: **descriptive tokenization structure for
115 fixed strings across the successful members of a predeclared, locally
available tokenizer roster**.

The census does not update Milestone 2, rescue the negative Llama 3.2 3B bridge,
select a causal layer, establish tokenizer-independent emoji structure, or
satisfy a Phase I paper gate. Later activation cells must keep tokenizer
structure as a measured covariate/control and must be frozen separately before
their outcomes are inspected.
