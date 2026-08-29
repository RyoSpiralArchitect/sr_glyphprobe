# Glyph-System Decomposition Atlas v0 (T11)

[日本語](GLYPH_SYSTEM_DECOMPOSITION_V0.ja.md) · [Completed exploratory result](GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.md) · [T10-D diagnostics](SEMANTIC_ATLAS_CROSS_MODEL_DIAGNOSTICS_V1.md) · [T10 result](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.md) · [Roadmap](ROADMAP.md)

Status: **frozen exploratory protocol; acquisition and discovery analysis completed**.

This document preserves the outcome-independent protocol. At its public freeze
there were zero T11 model forwards. The complete 73,566-forward discovery atlas
and its unforwarded 268-item reserve are reported separately in the
[T11 result](GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.md).

T11 asks:

> Does glyph-to-name correspondence track a glyph's compositional structure,
> presentation form, or whole-sequence lexicalization, and at which normalized
> depth or final-normalization boundary do the frozen model/tokenizer cells
> diverge?

This is the first lane that directly studies unusual multi-codepoint glyph
systems. It is prospective for its own activation outcomes but exploratory: it
has no confirmatory primary test. It cannot rescue T10 or establish meaning,
understanding, causality, mechanism, behavior, tokenizer independence, a scale
law, an instruction-tuning effect, or model generality.

## Why T11 changes the observable

T10's registered cross-model primary remains negative. T10-D nevertheless
found positive continuous retrieval margins in all 72 cells, model-specific
carrier-distance bottlenecks, strongly uneven item coverage, a weak codepoint
comparator, and model-conditioned changes at the final-norm boundary. At 292
items, T10's `0.02` minimum-cell floor was also a discrete six-net-item rule.

T11 therefore keeps minimum top-1 only for T10 comparability. Its main
descriptive observables are continuous item-level matched-label margins, MRR,
breadth and concentration, context stability, geometry, depth trajectories,
and raw-to-final change. This does not reinterpret T10; it asks a new question
with a new population.

## Pinned source and deterministic systems

The sole population source is Unicode Emoji 17.0 `emoji-test.txt`, pinned at:

- URL: `https://www.unicode.org/Public/17.0.0/emoji/emoji-test.txt`
- bytes: `669,326`
- SHA-256: `1d8a944f88d7952f7ef7c5167fef3c67995bcae24543949710231b03a201acda`
- fully-qualified entries: `3,944`

The source contains 1,184 single-codepoint entries and six disjoint unusual
systems under the frozen classifier: 207 presentation-selector sequences, 665
simple modifier sequences, 1,614 ZWJ sequences, 259 regional-indicator flags,
12 keycaps, and three tag flags.

Selection uses SHA-256 ranks under three fixed namespaces: one to sample within
each system, one to assign the reserve, and one to choose the depth subset. No
tokenizer or activation outcome enters selection.

## Fixed population and untouched reserve

The selected 1,111 items are:

| System | Prior-exposed anchor | T11 discovery | T11 reserve |
|---|---:|---:|---:|
| Single-codepoint atomic anchor | 64 | 0 | 0 |
| Presentation selector | 0 | 160 | 40 |
| Simple modifier | 0 | 192 | 64 |
| ZWJ composition | 0 | 256 | 96 |
| Regional-indicator flag | 0 | 160 | 64 |
| Keycap | 0 | 8 | 4 |
| Tag flag | 0 | 3 | 0 |
| **Total** | **64** | **779** | **268** |

The 64 atomic anchors are three-view calibrators. Every single-codepoint Unicode
Emoji 17.0 item was already forwarded in T8 or T9, so these anchors are labeled
`calibration_prior_exposed`, not new evidence. They are balanced at eight items
from each of eight non-flag Unicode groups.

T11 acquires 843 items: those 64 anchors plus 779 previously unused
multi-codepoint discovery sequences. The identities and source metadata of the
268 reserve items are public in the committed selection manifest; “untouched”
does not mean that their input strings are concealed. They may be tokenized as
a covariate check, but must receive zero model forwards and zero model-outcome
inspection in T11. After discovery analysis, a later T12 must freeze one
endpoint and its multiplicity family before any reserve model outcome is opened.

## Five fixed views

Unusual-system items have five strings:

1. `glyph`: the exact fully-qualified Unicode sequence;
2. `unicode_name`: the exact pinned Unicode name;
3. `component_name`: a deterministic component label;
4. `codepoint_literal`: the uppercase `U+...` sequence;
5. `decomposed_form`: a deterministic unfused or presentation-altered form.

Atomic anchors use only glyph, Unicode name, and codepoint literal. Missing
views are represented by an explicit mask and NaNs, never by copied or invented
text.

`component_name` is not a standardized alias or semantic ground truth. It uses
pinned emoji-test component names where available; only missing scalar labels
fall back to lowercase Unicode character names. ZWJ components are joined with
`" + "`; modifier bases and modifiers are named separately; regional
indicators become letter labels.

`decomposed_form` follows one frozen transform per system:

- remove VS15/VS16 for presentation pairs;
- insert spaces between base and modifier components;
- replace ZWJ with spaces while retaining the other scalars;
- map regional indicators to their two ASCII letters;
- keep only the base sign/digit for keycaps;
- map tag letters to lowercase ASCII for tag flags.

Every available view must remain unique within its analysis system, both as
Unicode text and as a token sequence in each model cell. Failure stops the cell
before model loading; no item is dropped or repaired.

## Matched incorrect-name controls

Codepoint text remains a weak comparator, not the sole negative control. For
each model/tokenizer, glyph system, and target view, T11 creates a deterministic
wrong-label mapping inside exact target-token-count strata. Each non-singleton
stratum is hash-sorted and cyclically shifted by one, so a label cannot map to
itself. The same rule is constructed independently inside the depth subset.

Required matched-control coverage is at least `0.75` for every distributional
analysis system. A stricter sensitivity mapping also matches the first target
token ID, but has no coverage gate and cannot replace the required mapping.
Coverage is checked before model weights load. Outcomes cannot trigger a new
mapping, looser stratum, item replacement, or threshold change.

Tag flags form a bounded three-item microcase. They receive the fixed views and
final endpoints, but no distributional or matched-control claim.

## Fixed transport and context grid

T11 reuses the full nine-cell T10 roster without outcome-based model selection:

- Llama 3.2 3B base;
- Qwen 2.5 base at 0.5B, 1.5B, 3B, and 7B;
- OLMo 2 1B base;
- Gemma 2 2B Instruct;
- SmolLM2 1.7B base;
- Mistral 7B Instruct v0.3.

Exact revisions and artifact manifests are inherited from the T10 freeze.
Architecture, size, tokenizer, corpus, and tuning remain confounded. Reusing
all nine cells preserves pairing and avoids selecting only the favorable T10
models.

Every available view uses two one-token carriers (`" a"` and `" |"`), eight
carrier repeats, and readout distances 1, 2, 4, and 8. Appending a carrier must
produce the raw view token IDs followed by eight identical carrier IDs. One
batch-one forward reads all four fixed positions. The runner checks for foreign
GPU compute before model loading and before every next shard.

The CUDA/BF16 furnace lane is intentional. It preserves the exact T10 model
artifacts and API endpoint semantics. T11 does not mix these results with the
separate MLX engineering lane.

## Broad endpoints and normalized-depth subset

All 843 acquired items store two endpoints from the same forward:

1. the raw output of the last decoder block, captured by a forward hook;
2. `output.hidden_states[-1]`, the API-returned final hidden state.

The second endpoint is often post-final-norm. Calling both endpoints
`resid_post` would erase the boundary T10-D showed to be model-conditioned.

A 192-item depth subset is fixed before any T11 forward: 24 atomic anchors
(three from each anchor group), 24 presentation sequences, 40 modifiers, 56
ZWJ sequences, 40 regional flags, and eight keycaps. The same forward stores:

- embedding output;
- inter-block states after `floor(0.25L)`, `floor(0.50L)`, and `floor(0.75L)`
  blocks;
- raw last-block output;
- returned final state.

These are normalized API depth fractions, not claims that architecture-specific
inter-block states are mechanistically identical sites.

## Cost, shards, and storage

The 843 acquired items contain 4,087 available item-view pairs. With two
carriers, each model performs 8,174 unique forwards; nine models perform 73,566
forwards. The broad atlas stores 65,392 present vectors per model, and the fixed
depth subset stores 43,776. Across nine models this is 982,512 present FP32
vectors.

Items are divided into 53 shards of at most 16 items per model, 477 shards in
total. Complete shards are atomically published and never reacquired. A partial
stage requires manual adjudication. The dense `.npy` arrays, including explicit
NaN slots for unavailable atomic views, are about 9.15 GiB before metadata.
They remain in the furnace data archive and are never committed to Git or put
on SpiralShare.

## Exploratory analysis contract

T11 has no primary hypothesis test. For each system, model, endpoint, carrier,
and distance it reports:

- paired cosine, top-1, MRR, paired-minus-off-diagonal margin, and linear CKA;
- correct-label minus token-length-matched wrong-label item margins;
- retrieval breadth and concentration;
- sign fraction, range, and median absolute deviation across all eight contexts;
- descriptive item-bootstrap intervals for median margins;
- raw-to-final and fixed-depth trajectories;
- cross-model per-view item-geometry CKA, cosine-map agreement, and item-margin
  agreement.

Retrieval breadth is the number of distinct top-1 targets reached, divided by
the number of targets in that system. Top-decile concentration is the fraction
of all predictions absorbed by the `ceil(0.10n)` most frequently predicted
targets. Both are reported forward and reverse. The stricter first-token-ID
matched mapping is analyzed separately as a sensitivity result, including the
case where its coverage is zero.

For each continuous margin, the returned-final-state atlas also gives a
balanced three-way sum-of-squares decomposition over model, glyph system, and
the eight carrier-distance contexts, with every two-way interaction and the
three-way residual retained. This is descriptive heterogeneity accounting, not
an inferential random-effects model. Each depth-cell trajectory records the
first descriptive bootstrap interval that excludes zero, if any, plus the
returned-final minus raw-last-block median change.

Three control-adjusted contrasts operationalize the question:

- `lexicalization`: glyph→official-name advantage minus
  glyph→component-name advantage;
- `presentation_or_fusion`: glyph→official-name advantage minus
  decomposed-form→official-name advantage;
- `component_tracking`: decomposed-form→component-name advantage minus
  glyph→component-name advantage.

They are operational contrasts, not direct measurements of meaning. Minimum
top-1 is secondary and cannot be used to revise T10.

## Predeclared landing patterns

T11 preserves six possible clean outcomes: a compositional candidate, a
whole-sequence lexicalization candidate, a presentation/final-norm boundary, a
model-conditioned atlas, a tokenizer-structural account after matched controls,
or a broad bounded null. The analysis records evidence for each branch but does
not select an authoritative scientific conclusion automatically.

Any positive T12 claim requires a new freeze before the 268 reserve items are
forwarded. A broad null is retained as the boundary that T8-T10's alignment did
not extend to unusual glyph systems.

## Furnace sequence

The committed freeze is audited first. On the furnace, all nine tokenizer and
artifact preflights run with zero model forwards, then one aggregate preflight
binds their hashes. Only after a fresh contention check may the resumable
acquisition begin.

```bash
python scripts/glyph_system_decomposition_v0.py audit-freeze

python scripts/glyph_system_decomposition_v0.py preflight-all \
  --output <preflight-dir>

python scripts/glyph_system_decomposition_v0.py run \
  --model-label <role> \
  --preflight-directory <preflight-dir> --output <runs-root>/<role>

python scripts/glyph_system_decomposition_v0.py finalize \
  --model-label <role> --preflight-directory <preflight-dir> \
  --run <runs-root>/<role>

python scripts/glyph_system_decomposition_v0.py summarize \
  --run <runs-root>/<role> --preflight-directory <preflight-dir> \
  --output <summaries-root>/<role>

python scripts/glyph_system_decomposition_v0.py analyze \
  --runs-root <runs-root> --summaries-root <summaries-root> \
  --output <analysis-dir>

python scripts/glyph_system_decomposition_v0.py validate-analysis \
  --analysis <analysis-dir>
```

The operator must run `spiral status` immediately before remote compute and
yield if contention appears. `run` accepts `--shard-start` and `--shard-stop`;
subsequent invocations validate and skip complete shards. The runner also
yields between completed shards. `preflight-all` and `run` resolve only the
pinned revisions already present in the local Hugging Face cache and never
download. For a nonstandard cache layout, the single-cell commands accept an
explicit `--model-path`; all nine receipts must still be assembled before any
weight load.
