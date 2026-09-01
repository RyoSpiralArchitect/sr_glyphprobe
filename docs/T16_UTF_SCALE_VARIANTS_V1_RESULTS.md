# T16-UTF-X1 scale and sequence-variant results

[日本語](T16_UTF_SCALE_VARIANTS_V1_RESULTS.ja.md) · [Frozen protocol](T16_UTF_SCALE_VARIANTS_V1.md) · [Compact analysis](../validation/t16_utf_scale_variants_v1/results/analysis.json) · [Closeout](../validation/t16_utf_scale_variants_v1/closeout.json)

## Result in one paragraph

The earlier tokenizer-conditional separation between exact repetition,
within-construction mixing, and cross-construction mixing survived a much
larger stress test. T16-UTF-X1 completed 515,808 factorial records across nine
fixed model/tokenizer cells, four depths, 19 sequence lengths through
`n=500`, six Unicode construction systems, six order variants, five
separators, and three singleton-anchor positions. The primary
cross-minus-within scale summary was positive in all 36 model-by-depth cells,
and all 36 system-stratified bootstrap intervals lay above zero. The same sign
held at every one of the 18 nontrivial lengths in all 36 cells, including
`n=500`. This was not a monotone scaling curve: no cell increased at every
successive length. Exact-multiset order controls exposed a second, cleaner
pattern. Grouping repeated items into contiguous blocks produced the largest
order displacement in all 72 model-by-depth-by-diversity-family cells, while
99.75% of all order pairs had identical full-prompt token multisets. Anchor
position and separator choice also mattered, but with different length
profiles and weaker tokenizer controls. These are exploratory hidden-state
geometry results, not evidence for tokenizer-independent Unicode structure,
emoji meaning, a scaling law, or a causal circuit.

## Completed surface

- Nine cached cells: four Qwen2.5 sizes, OLMo 2 1B, SmolLM2 1.7B, Gemma 2
  2B IT, Llama 3.2 3B, and Mistral 7B Instruct v0.3.
- 57,312 records and 57,120 unique prompts per model; 515,808 records and
  514,080 model-by-chunk unique prompts in total.
- Four raw decoder-block outputs at normalized depths 0.25, 0.50, 0.75, and
  1.00, captured at the final common wrapper token.
- Zero generation calls and zero interventions.
- Ninety-nine atomic chunks; every ledger count, hidden shape, finite-value
  check, and file hash passed before integrated scientific opening.

The nine model cells share training and tokenizer ancestry in several ways.
They are a fixed stress-test roster, not nine independent replications.
Hidden-state magnitudes also do not share an absolute scale across models.

## Scale: cross-construction excess persisted

Each table entry is the median over 96 system-by-rotation-by-wrapper principal
units. Within each unit, all 18 nontrivial lengths are averaged before the
median is taken. Brackets give the equal-tailed 95% interval from 10,000
system-stratified bootstrap replicates.

| Model | 0.25 | 0.50 | 0.75 | 1.00 |
|---|---:|---:|---:|---:|
| Gemma 2 2B IT | `0.020312` [0.017202, 0.025056] | `0.058764` [0.050896, 0.069032] | `0.049046` [0.036993, 0.055737] | `0.008846` [0.007089, 0.010369] |
| Llama 3.2 3B base | `0.026651` [0.023856, 0.028785] | `0.039728` [0.030946, 0.044741] | `0.027569` [0.022443, 0.030803] | `0.017638` [0.016450, 0.020952] |
| Mistral 7B Instruct v0.3 | `0.034532` [0.030893, 0.037246] | `0.044824` [0.040131, 0.048745] | `0.050963` [0.044785, 0.057629] | `0.044963` [0.037655, 0.054033] |
| OLMo 2 1B base | `0.020657` [0.019697, 0.022988] | `0.033857` [0.030269, 0.035322] | `0.027274` [0.024622, 0.030640] | `0.016683` [0.014908, 0.019532] |
| Qwen2.5 0.5B base | `0.010588` [0.009715, 0.012951] | `0.013317` [0.010426, 0.015523] | `0.011273` [0.009704, 0.012597] | `0.016596` [0.013864, 0.021645] |
| Qwen2.5 1.5B base | `0.009861` [0.007280, 0.011371] | `0.012645` [0.010250, 0.015391] | `0.015657` [0.012144, 0.019857] | `0.016580` [0.014121, 0.019964] |
| Qwen2.5 3B base | `0.017373` [0.014882, 0.018959] | `0.014943` [0.013301, 0.016897] | `0.016141` [0.013709, 0.017549] | `0.011379` [0.009923, 0.013163] |
| Qwen2.5 7B base | `0.023156` [0.020300, 0.027325] | `0.025414` [0.021644, 0.029092] | `0.031505` [0.022767, 0.033990] | `0.025975` [0.025356, 0.033461] |
| SmolLM2 1.7B base | `0.006857` [0.006257, 0.007531] | `0.012381` [0.011084, 0.014369] | `0.010516` [0.009138, 0.011179] | `0.011871` [0.008253, 0.013221] |

At `n=500`, cross-minus-within remained positive in all 36 cells, ranging
from `0.010529` to `0.069266`. Positive principal units ranged from 78/96 to
96/96 across cells, with a median of 92/96. The aggregate sign is therefore
stable, but unit-level heterogeneity is real.

Length did not behave like a simple scale law. The `n=256` value exceeded the
`n=16` value in 30/36 cells, and `n=500` exceeded `n=16` in 27/36. Yet only
17/36 cells increased from `n=384` to `n=500`, and none was nondecreasing over
all 18 nontrivial lengths. Peaks occurred at `n=384` in 13 cells, `n=500` in
9, `n=256` in 6, and earlier lengths in the remaining 8. Within the four
Qwen2.5 sizes, only the 0.75-depth row was strictly ordered by parameter count.
The result supports persistence under longer sequences, not a parameter- or
length-scaling law.

The two parent T16-UTF roles retained the same sign at `n=2,4,8,16` in all 32
reacquired model-depth-length cells. The largest absolute change in a per-`n`
median was `0.002347` for Gemma and `0.001339` for Mistral. This is a
descriptive reacquisition under a different batch composition, not a frozen
numerical-parity test or an independent replication.

## Exact-multiset order: blocked runs dominated

Every order pair keeps the anchor first and preserves the exact UTF item
multiset. It compares forward cycling with reversal, contiguous blocking,
end-interleaving, or one of two frozen shuffles at fixed family, length,
separator, wrapper, and anchor.

Across nine models, 258,544 of 259,200 order pairs (99.7469%) also preserved
the exact full-prompt token multiset. All 28,800 pairs were exact token-multiset
matches in eight models. Gemma matched 28,144/28,800; its contrast-specific
rates ranged from 95.56% to 100%.

Three patterns were unusually consistent:

- `blocked_tail`, which groups repeated glyphs into contiguous runs, produced
  the largest displacement in all 72 model-by-depth-by-within/cross cells. Its
  median ratio to the largest competing order variant was 1.88, with a range
  of 1.07 to 4.81.
- Cross-construction order displacement exceeded within-construction
  displacement in all 180 model-by-depth-by-order-variant comparisons.
- The blocked displacement at `n=256` exceeded its `n=8` value in all 72
  model-by-depth-by-family cells. Reversal and interleaving did not show that
  universal accumulation.

This lane supplies strong evidence that token order and local clustering alter
the captured state even when the token inventory is fixed. It does not rescue
the scale lane from its tokenizer boundary and does not identify Unicode
family semantics.

## One exact anchor: recency-like geometry without accumulation

The position lane places exactly one anchor first, middle, or last against a
fixed within- or cross-construction background. Each paired comparison keeps
the exact UTF item multiset fixed.

- Cross-background displacement exceeded within-background displacement in
  all 72 model-by-depth-by-position comparisons.
- Moving the anchor last displaced the state more than moving it to the middle
  in 71/72 model-by-depth-by-family cells. The sole reversal was Qwen2.5 0.5B
  at the final block under the cross background: middle `0.016530`, last
  `0.016377`.
- Unlike blocked order, the position effect usually did not grow with length.
  `n=256` exceeded `n=8` in 0/36 within-middle, 6/36 within-last, 2/36
  cross-middle, and 8/36 cross-last cells.

Full-prompt token multisets matched in 77,952/103,680 position pairs (75.19%).
Mistral matched all 11,520 of its pairs. Other models ranged from 63.33% to
88.33% in aggregate. The Mistral cell is therefore the cleanest evidence that
moving the same token inventory changes the captured state; the cross-model
summary remains tokenizer-conditional.

## Separators: large but deliberately unresolved

Relative to no separator, newline was the largest separator displacement in
26/36 model-depth cells, comma-space in 6, and ASCII pipe in 4. ASCII space
was never largest. Newline led at all nine 0.25-depth cells and eight of nine
0.50-depth cells. Separator displacement generally accumulated with length:
`n=256` exceeded `n=8` in 36/36 ASCII-space, 32/36 comma-space, 32/36 newline,
and 29/36 pipe cells.

No separator pair preserved the exact full-prompt token multiset. These values
combine a visible delimiter intervention with changed tokenizer paths and must
not be interpreted as tokenizer-independent punctuation geometry.

## Tokenization boundary and construction heterogeneity

Scale pairs never preserved the exact full-prompt token multiset. Exact token
counts were common for within-family Qwen pairs but sparse for cross-family
pairs: the cross-family count-match rate ranged from 0.93% in Qwen to 28.24%
in Gemma. Consequently, the 36/36 scale sign cannot establish that Unicode
construction family survives token-identity matching.

Construction systems were also heterogeneous. Keycaps had the largest
cross-minus-within system median in 25/36 cells, regional-indicator flags in
8, and presentation sequences in 3. The atomic-scalar median was slightly
negative in two Qwen2.5 0.5B late cells even though both complete 96-unit cell
medians were positive. The full result is therefore not a universal positive
for every construction system at every depth.

## Execution qualification

The scientific run used the pushed freeze commit `fcf73bd` and completed in
8,039 seconds. Six CUDA allocator retry warnings occurred—three during Gemma,
one during Qwen2.5 3B, and two during Qwen2.5 7B. None became a Python
exception or an incomplete chunk. Every admitted array subsequently passed
finite-value, shape, row-count, and SHA-256 validation. The warnings remain in
the committed run log and the closeout; this is not described as a warning-free
run.

An earlier three-chunk engineering canary from commit `7a99494` used a larger
padded-token budget. It remains preserved as engineering-invalid evidence and
is excluded from every scientific result.

## Claim boundary and evidence

T16-UTF-X1 has no binary scientific gate. Its strongest result is a stable,
tokenizer-conditional separation accompanied by a nearly token-multiset-exact
order effect. It does not authorize claims about emoji meaning, causal
implementation, tokenizer-independent Unicode composition, instruction-tuning
effects, parameter scaling, or model-population generality.

- [Compact analysis](../validation/t16_utf_scale_variants_v1/results/analysis.json), SHA-256 `988f2689565b9d45741f8f342cf49a3b54bd3d8d88f570f1693f21756f6d3e12`
- [Closeout](../validation/t16_utf_scale_variants_v1/closeout.json)
- [Execution log](../validation/t16_utf_scale_variants_v1/run.log), SHA-256 `9e09603ea4771c5552b9e27c66e33438858120617dc3c053a4b4e0643cb55b0d`
- [Tokenizer preflight](../validation/t16_utf_scale_variants_v1/tokenizer_preflight.json)

The 20.31 GB raw run remains in the recorded furnace scratch root. Raw hidden
arrays were not copied into Git.
