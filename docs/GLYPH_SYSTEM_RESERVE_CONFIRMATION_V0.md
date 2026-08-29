# Glyph-System Reserve Confirmation v0 (T12)

[日本語](GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0.ja.md) · [T11 results](GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.md) · [T11 protocol](GLYPH_SYSTEM_DECOMPOSITION_V0.md) · [Roadmap](ROADMAP.md)

Status: **prospective protocol; zero T12 reserve model forwards**.

T12 is a one-shot confirmation using the complete T11 reserves for the two
clearest unusual-glyph candidates. It deliberately widens the T11 suggestion
from ZWJ alone to a two-hypothesis family:

1. **H_ZWJ_FUSION:** a fused ZWJ sequence has a larger matched-control-adjusted
   relation to its official name than its space-separated decomposition does;
2. **H_REGIONAL_DUAL:** a regional-indicator flag simultaneously favors its
   official place name in fused form and its letter-component label in ASCII
   decomposed form.

The Regional hypothesis is one intersection-union claim, not two opportunities
to declare success. Both component tests must pass. Holm correction is then
applied across `H_ZWJ_FUSION` and `H_REGIONAL_DUAL`.

## Why Regional is included

T11 found the ZWJ `presentation_or_fusion` contrast to be the least diffuse
single candidate: 65/72 cells were positive, eight of nine model-level context
medians were positive, and no cell had a descriptive interval strictly below
zero. Regional flags showed a different and scientifically useful pattern.
Their fused form favored the official place name, while their ASCII
decomposition favored the component-letter label. The discovery medians were
`0.0668` and `0.0441`, respectively.

Including Regional makes the confirmatory question sharper rather than merely
larger. T12 can distinguish a fused-form advantage from a dual
whole-sequence/component organization. The cost remains bounded because the
reserves contain only 96 ZWJ and 64 regional-flag items.

## Fixed population and acquisition

The 160 identities were selected and published before T11 acquisition. They
received zero model forwards in T11, and their model outcomes remain
uninspected at this freeze.

| System | Complete reserve | Forwarded views |
|---|---:|---|
| ZWJ sequence | 96 | glyph, Unicode name, decomposed form |
| Regional-indicator flag | 64 | glyph, Unicode name, component name, decomposed form |

T12 reuses the same nine pinned model/tokenizer cells, two one-token carriers,
and four readout distances as T11. Only `output.hidden_states[-1]` is stored.
No raw-last-block or intermediate-depth endpoint is acquired, so an alternative
endpoint cannot rescue a failed primary result.

There are 544 item-view pairs. With two carriers, each model performs 1,088
unique forwards; the full roster performs 9,792. Each forward supplies all four
distances. The stored result contains 39,168 FP32 readout vectors, no
interventions, and no generations.

## Matched controls

For each tokenizer, system, and label view, the required incorrect label is
chosen inside the exact target-token-count stratum. A second mapping also
matches the first target token ID. Both use a deterministic one-step cycle
after hash sorting, and neither permits self-matches.

Required-control coverage must be at least `0.75`; first-token-matched coverage
must be at least `0.70`. Every map is fixed before model weights load. A failed
coverage gate stops that model cell. Outcomes cannot trigger a new map,
replacement item, relaxed stratum, or lower threshold.

For query form `q`, target label `t`, and its deterministic wrong label `w`,
the item-level adjusted relation is

`cos(q_i, t_i) - cos(q_i, t_w(i))`.

The fusion contrast subtracts the decomposed-form relation from the glyph
relation to the official name. Component tracking reverses the query order for
the component label.

## Registered tests

All 72 model × carrier-distance cells remain in each elementary test. The cell
statistic is the median eligible item contrast. The global statistic is the
median of those 72 cell medians. Its null distribution uses 49,999 shared
within-item swaps of the glyph and decomposed query forms. One swap is shared
across every model and context for the same Unicode item, preserving the
cross-context and cross-model dependence attached to that item.

| Elementary test | Practical floor |
|---|---:|
| ZWJ presentation/fusion | `0.005` |
| Regional presentation/fusion | `0.02` |
| Regional component tracking | `0.02` |

The floors are discovery-informed and were fixed before any reserve forward.
They are lower than the corresponding T11 discovery medians but remain above a
mere positive floating-point sign.

Pooling alone cannot declare success. Every elementary test must also satisfy:

- at least six of nine model summaries meet its practical floor;
- at most one model summary is at or below the negative practical floor;
- the first-token-matched global statistic is positive; and
- at least six first-token-matched model summaries are positive.

Each model summary is the median of its eight context-cell medians.
First-token sensitivity cannot rescue a failed required-control test.

For `H_REGIONAL_DUAL`, the hypothesis p-value is the maximum of the fusion and
component-tracking p-values, and both component gates must pass. Holm's method
controls the familywise error rate at `0.05` over the two registered
hypotheses. A hypothesis is confirmed only when its Holm decision and every
practical, heterogeneity, and strict-prefix gate agree.

## Outcome branches

T12 closes both reserve questions even if neither is confirmed. The clean
landing patterns are:

- both candidates reproduce;
- ZWJ fusion reproduces but the Regional dual conjunction does not;
- Regional dual structure reproduces but ZWJ fusion does not;
- neither reproduces under the frozen rule; or
- acquisition or a mandatory validity gate fails, leaving no scientific
  decision.

Component-only Regional success is reported as a failed conjunction, not as a
confirmed Regional hypothesis. Model- or context-specific positives remain
descriptive when the registered gate fails.

## Claim boundary

A positive T12 result supports reproducibility of an operational activation-
geometry contrast in this fixed nine-cell roster and transport grid. It does
not establish emoji meaning, understanding, causality, mechanism, behavioral
steering, tokenizer independence, a scale law, instruction-tuning effects,
architecture generality, model-population generality, or independent
replication. It cannot rescue or alter T10.

The next question—whether emoji-derived steering is special relative to
matched words, non-emoji Unicode symbols, punctuation, and generic token
directions—must be studied in a separate exploratory protocol after the T12
primary result is sealed. T12 reserve outcomes cannot be used to modify this
protocol.

## Furnace sequence

The committed freeze is audited first. All nine tokenizer and artifact
preflights then run with zero reserve model forwards. Immediately before
compute, the operator must check furnace contention and yield if another GPU
workload appears.

```bash
python scripts/glyph_system_reserve_confirmation_v0.py audit-freeze

python scripts/glyph_system_reserve_confirmation_v0.py preflight-all \
  --output <preflight-dir>

python scripts/glyph_system_reserve_confirmation_v0.py run \
  --model-label <role> --preflight-directory <preflight-dir> \
  --output <runs-root>/<role>

python scripts/glyph_system_reserve_confirmation_v0.py finalize \
  --model-label <role> --preflight-directory <preflight-dir> \
  --run <runs-root>/<role>

python scripts/glyph_system_reserve_confirmation_v0.py analyze \
  --runs-root <runs-root> --preflight-directory <preflight-dir> \
  --output <analysis-dir>
```

Completed shards are validated and skipped. An incomplete stage requires
manual adjudication. Models resolve only from the pinned local furnace cache;
the runner never downloads them.
