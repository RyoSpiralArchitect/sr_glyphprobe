# T21: A conditional attention-message contribution to keyword similarity

[日本語](T21_GLYPH_CONTEXT_PATH_RESULTS_V0.ja.md) | [Prospective confirmation protocol](T21_GLYPH_CONTEXT_PATH_CONFIRMATION_V0.md)

Status: **confirmation completed and independently reconstructed**. The claim
is a conditional contribution to cosine margin in one model. Absolute
glyph-message decrement and restoration have zero mean top-1 effects. T19/T20 verdicts
remain unchanged.

## Result

T21 first reused the 384 T20 evaluation items as an explicitly exploratory
pilot. Both candidate anchors passed its screen; the recorded selection rule
chose block 21. We then specified a separate confirmation before reconstructing
or tokenizing the remaining 195 items. All 195 were included, with no outcome
exclusions. The keyword gallery, two deterministic token-count-matched donors,
and Llama 3.2 3B BF16 artifact were unchanged.

The readout residual after block 21 was replaced by the same item's
codepoint-view state. Subsequent blocks 22–27 received donor post-RoPE keys
and values at selected past positions **only for the readout query**. The
primary readout was distance 8 under both pipe and article carriers. Effects
use neutral-path references in identical batch slots, retaining the residual
reset. Each item averages its two carriers and two donors; n is **195**.

| Primary contrast | Mean cosine-margin effect | One-sided simultaneous 95% lower bound |
| --- | ---: | ---: |
| Full-prefix replacement calibration | 0.008926 | 0.006430 |
| Glyph-message decrement | 0.003422 | 0.002303 |
| Decrement beyond equal-count suffix control | 0.002326 | 0.001399 |
| Glyph-message restoration | 0.003717 | 0.002757 |
| Restoration beyond equal-count suffix control | 0.002267 | 0.001400 |

All five lower bounds exceed zero under the specified single-step max-t
item-bootstrap procedure (20,000 shared-index draws; seed 2026092201;
critical value 2.1843314564). The resulting verdict is
`conditional_path_contribution_supported`. The five comparisons share
conditions and are correlated; they are not five replications.

The two position-adjusted means are 26.05% and 25.40% of the mean full-prefix
reference decrement. Those ratios are descriptive scale comparisons, not
fractions of explained variance or recovered semantic knowledge. All primary
means remain positive after removing the largest 5% of item effects, and
each carrier has positive means separately; those are secondary diagnostics.

## A consequential boundary: margin and retrieval rank diverge

The average keyword top-1 effect is exactly **0** for absolute glyph-message
decrement, absolute restoration, and position-adjusted restoration. The
position-adjusted decrement is −0.001282 in top-1 units. These are descriptive
means, not equivalence tests. The full-prefix calibration changes top-1 by
0.010256. Thus the positive primary result concerns movement of relative
keyword similarity, with no corresponding mean top-1 improvement in the
glyph-message contrasts. No generated response or downstream task was tested.

T21 does not demonstrate an emoji-specific mechanism: a non-emoji symbol
panel was not subjected to this path intervention. It also does not establish
a complete or unique circuit, natural-context generality, unconditioned
necessity/sufficiency, behavioral steering, or a new cross-model causal result.
The test is conditional on a codepoint-view residual reset, two carriers, a
fixed source/gallery pool, and one checkpoint. Equal-count suffix controls
do not match attention mass or semantic content. The intervals describe an
approximate item-resampling model over the eligibility-defined remaining
population, not every emoji or donor population.

## Prospective order and integrity

| Event | UTC, 2026-09-02 | Record |
| --- | --- | --- |
| Pilot acquisition complete | 03:56:14 | 384 already exposed items |
| Confirmation design specified | 04:24:25 | Design SHA-256 `4c0609181e961555b850e2dded02b218d4e9c7511541c135efa1467eb81f0330` |
| Confirmation-runner canary complete | 04:26:33 | Exact replay of the original eight exposed pilot items |
| 195-item specification created | 04:26:59 | SHA-256 `c3c34ca583958882157b90c20a28ef1667138b9dd0df907f95aa4c8d29ab8282` |
| First confirmation item started | 04:28:34 | Exact input specification already published |
| All 195 confirmation items complete | 04:30:17 | 118.50 seconds; no interruption |

The selection replay verified the original 1,064 candidates, 954 matched emoji,
55 reserved symbol aliases, and every one of 759 previously used allocations.
The remaining set has 43 two-token and 152 three-token glyphs. No protected
historical target bank was read. Freshness concerns T19/T20/T21 evaluations;
earlier studies and pretraining are outside that claim. The original matched
pool now has **zero further unused items** after these allocations.

The independently implemented validator ran on a separate CPU host against the
GPU-acquired arrays. Its largest metric discrepancy was 1.255 × 10⁻¹⁴;
all top-1 arrays were exactly equal. The max-t critical value differed by
5.995 × 10⁻¹⁴, and the five bounds and final verdict agreed. This is an
independent numerical reconstruction, not a second scientific replication.

The confirmation used 2,720 batched forward calls representing 70,580 sequence
forwards, including source capture and parity checks; no generation or model
training occurred. The 384-item pilot used 4,610 calls / 138,242 sequences in
218.87 seconds. Both stages used the already present checkpoint. Raw arrays
remain under the run directories and are excluded from Git and the compact
anonymous package. Compact results and the acquisition/analysis/validation
receipts are in `validation/t21_glyph_context_path_confirmation_v0/results/`.

## Replay the compact inference

The repository and anonymous archive include all 195 items' five primary
margin contrasts and corresponding top-1 contrasts in `item_contrasts.json`.
With NumPy installed, run from either root:

```bash
python3 scripts/validate_t21_compact_inference_v0.py \
  --compact validation/t21_glyph_context_path_confirmation_v0/results/item_contrasts.json \
  --result validation/t21_glyph_context_path_confirmation_v0/results/confirmation_result.json
```

The separate statistical implementation reproduces the 20,000-draw critical
value, five means and lower bounds, top-1 means, and verdict with maximum
numeric error 0 in the recorded environment. This checks inference from
derived scalar contrasts. The raw-state intervention reconstruction described
above is a distinct check and requires the omitted model-dependent arrays.

## Manuscript and next questions

Table 6's seven dashes meant “outside the primary verdict family,” not missing
runs. They are now explicitly labelled `secondary`, with all numerical values
and historical verdicts preserved.

T21 supplies a narrow positive extension: late attention from glyph positions
contributes to lexical similarity under a specified state intervention. The
next independent study should compare the same route for non-emoji symbols,
separate keys from values, and connect margin movement to retrieval ranks or
generated behavior. Those designs require a newly reserved population and
separate prospective choices. The current 195 items cannot be reused as an
untouched confirmation set.
