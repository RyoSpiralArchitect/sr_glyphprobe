# Before asking what an emoji means, ask whether it leaves a fingerprint

[Mistral base depth-distance results](MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.md)

[日本語](NOTE.ja.md) · [T15-A emoji × word result](EMOJI_WORD_INCONGRUENCE_INTERACTION_V0_RESULTS.md) · [T14-X / T14-C result](EMOJI_STEERING_T14_X_T14_C_RESULTS_V0.md) · [T12 reserve result](GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.md) · [T13 decision map](EMOJI_STEERING_SPECIFICITY_ATLAS_V0.md) · [T11 exploratory result](GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.md) · [T11 frozen protocol](GLYPH_SYSTEM_DECOMPOSITION_V0.md) · [T10 diagnostics](SEMANTIC_ATLAS_CROSS_MODEL_DIAGNOSTICS_V1.md) · [Dense CUDA results](MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.md) · [Carrier-distance results](MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.md) · [Common-suffix results](MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.md) · [Matched-slot geometry results](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.md) · [Multifamily geometry results](MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.md) · [Tokenizer census results](MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.md) · [E2 MPS transport v2 protocol](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.md) · [v1 preflight failure](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.md) · [Holdout status](HOLDOUT_STATUS.md) · [E2 Stage-A3 numeric-screen result](LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.md) · [E2 Stage-A v2 result](LLAMA32_3B_MLX_VALIDATION_RESULTS.md) · [E1 exploratory results](EMOJI_FAMILY_EXPLORATORY_RESULTS.md) · [Milestone 2 results](MILESTONE2_RESULTS.md) · [Baseline results](RESULTS_V1.md) · [Research roadmap](ROADMAP.md)

An emoji looks like an unusually convenient probe for a language model. It is small, familiar, and visually distinctive. That convenience is also a trap. The moment a model reacts differently to 🟤 and 🟣, it is tempting to tell a story about brownness, purpleness, circles, or squares.

GlyphProbe begins one step earlier.

Its first question is not what an emoji means inside a model. It asks whether a direction derived from that emoji leaves a reproducible fingerprint when added to a fixed internal activation. If the intervention magnitude, source prompts, target prompts, clipping, and random controls are all sealed, does the same direction move the next-token distribution in a recognizable way on held-out prompts?

That is a smaller question, but it has sharper failure modes.

## Building the map before naming the territory

The first panel contains ten glyphs: five colors, each represented by a circle and a square. Multiple source wrappers produce an activation direction for each glyph. Those directions are centered against the panel, normalized by RMS, and added at selected GPT-2 decoder layers. The output is not interpreted token by token. Instead, the full-vocabulary logit change is compressed into a deterministic, unit-normalized fingerprint.

The design then asks whether a glyph's fingerprint is more similar to itself across held-out target prompts than it is to other glyphs or to norm-matched random directions outside the panel span. Separate wrapper subsets estimate the source direction again. A zero-vector intervention checks whether the hook itself changes anything. A dose grid and sign flip test basic local behavior.

This produces a map of repeatability before interpretation.

## Why MLX entered the experiment

The standard run contains 14,208 intervention and control records. On Apple silicon, that made MLX a practical candidate, but using the same model name in two libraries does not guarantee the same numerical experiment. The MLX path was therefore qualified against Transformers on the exact pinned GPT-2 revision, in FP32, at the same `resid_post` layers.

The qualification covers four prompt lengths and four layers. It checks token IDs, baseline activations and logits, exact zero-hook behavior, and the magnitude and direction of a fixed non-zero intervention. All 80 gates passed. In the recorded synchronized end-to-end benchmark, median latency fell from 17.52 ms with Transformers/MPS to 10.73 ms with MLX, about 1.63× faster.

That speedup belongs to this machine, software stack, model, prompt-length grid, and measurement boundary. It is useful engineering evidence, not a general law about MLX.

One later run also records why timing needs that boundary. The first matched-null A foreground process was externally interrupted after 798 rows under severe machine load: median latency was about 309 ms rather than the 10.73 ms baseline. A sealed resume completed the exact 14,208-row grid without duplicate or missing rows or errors, with zero-hook activation/logit RMS at 0; later latency returned to about 12.43 ms. This is operational provenance, not evidence about the model or a universal speed result. The P2, independent-source, and diagnostic runs completed normally.

## What the first run showed

The standard MLX run completed without recorded errors and passed all 11 readiness checks. Its median held-out fingerprint advantage was 0.608, and the median cross-seed advantage was 0.931. The source directions aligned strongly across wrapper subsets. The intended intervention magnitude was matched to numerical precision. The dose response was monotone in the reported median, sign flips were nearly antisymmetric, and the explicit zero hook was an exact no-op in the recorded metrics.

Those are encouraging properties for a candidate map.

They are not the whole result. Eleven of the 36 layer–seed–strength cells were non-positive. Every layer had a positive median, but every layer also contained at least one negative cell. The strongest single row depended on a broad random-control separation distribution, so it is not the headline. The median, positive rate, ranges, and cross-seed aggregates are more honest summaries.

The permutation screen also reached its finite floor, `1/1001`, in every cell. That is a useful exploratory flag, but it is not a multiplicity-corrected global significance result.

## The matched controls changed the picture

Milestone 2 addressed part of the tokenization warning with three null panels. Every panel has ten conditions, three raw GPT-2 tokens per symbol, and the same prespecified 9:1 panel-prefix structure as the colored shapes. This is deliberately narrower than token-identity matching: identical token IDs would decode to the same bytes and cease to be a distinct glyph input. Panel C also contains one declared semantic-near control, the nonreference red square `🟥`, because the eligible non-colored pool was one symbol short of the 27 disjoint dominant-prefix slots.

On the original 24-target exploratory matrix, the colored-shape score exceeded the median of panels A/B/C by `0.047427` at the median of 36 paired cells. Twenty-five cells were positive and 11 were nonpositive. The 48-, 32-, and 24-dimensional same-seed algebraic folds gave `0.040200`, `0.028907`, and `0.048591`. These are descriptive comparisons, not independent cells, a percent-explained estimate, or CountSketch-seed sensitivity.

The more important result came from the frozen 48-target P2 bank. At layer 2, the mean adjusted target effect was `+0.208363`, with a frozen-v1 95% interval of `[0.137463, 0.276893]` and Holm-adjusted `p = 0.00143999`. With the independently written source wrappers it was `+0.187507`, `[0.125489, 0.247659]`, `p = 0.00393996`. Both received the v1 label “robust to the prespecified matched controls.”

Layer 4 told a different story. Its primary-source estimate was `-0.0329465`, `[-0.0761085, 0.0110094]`; the independent-source estimate was `-0.086379`, `[-0.159246, -0.016917]`. Both were unresolved under the frozen rule. The result is therefore mixed and layer-specific, not a global success.

## Auditing the analysis after the result

The v1 analyzer checks the frozen target bank, model cell, condition grids, target sampling unit, and hypothesis family. But it assigns primary and null roles from command-line order. A separate binding audit was needed to prove that all 14 published run directories—the 12 core exploratory, P2, and independent-source arms plus two diagnostics—actually map to the intended frozen configs, panels, sources, targets, paths, and hashes. That audit passed.

There is a second qualification. The v1 interval resamples target effects after the leave-one-group-out prototypes have been built once. It does not rebuild those data-dependent prototypes inside each bootstrap replicate. A post-hoc sensitivity analysis did rebuild all prototypes jointly. For the primary source, its intervals were `[0.099930, 0.295380]` at layer 2 and `[-0.099995, 0.041902]` at layer 4. For the independent source they were `[0.104210, 0.271322]` and `[-0.185084, 0.007648]`.

Those wider intervals are useful, but the method was specified after P2 outcomes were available. It assigns no p-value or confirmatory status and does not overwrite v1. The [technical result](MILESTONE2_RESULTS.md) keeps the two inferential layers separate.

The two secondary token-structure diagnostics also completed. Each covered 14,208 rows with zero errors, zero-hook activation/logit RMS of 0, and readiness 11/11. Their random-adjusted headline `emoji_fingerprint_advantage` values were `+0.751225` for the suffix-matched panel and `+0.601038` for the prefix-homogeneous panel. Those headline values are not the raw separation scores used for the paired comparison.

At CountSketch dimensions 96, 48, 32, and 24, the median standard-minus-suffix raw separation was `+0.002624`, `+0.009473`, `+0.004026`, and `+0.009700`. The corresponding standard-minus-prefix values were `+0.022096`, `+0.023254`, `+0.011040`, and `+0.025387`. At 96 dimensions, 20/36 suffix cells and 25/36 prefix cells were positive. These are post-hoc descriptive diagnostics, not inferential or equivalence tests. The lower-dimensional results are same-seed algebraic folds, not independent reruns or seed sensitivity.

## A controlled family substitution exposed shared transfer

The E1 side track asked a different, narrower question. Five ten-emoji blocks
were selected so that every matched slot has the same first and third GPT-2
tokens; only the family-middle token changes. That makes the token structure
unusually controlled, but it also makes family identity inseparable from the
middle token. E1 was frozen before five MLX runs and reused only the 24 already
explored prestage targets. E1 read neither P2 nor C1.

The complete source-family × prototype-family matrices were broadly positive.
Their 25 mean cells ranged from `0.395455` to `0.484915` at layer 2 and from
`0.602564` to `0.681909` at layer 4. Yet the equal-family within-family excess
was only `0.014752595564` at layer 2 and `0.014887989201` at layer 4. Every
family-specific descriptive interval crossed zero. The layer-4 negative
comparator was not negative, and 10/30 family × layer × seed cells failed to
exceed random controls.

The most useful reading is not that GPT-2 discovered five semantic emoji
families. It is that much of the matched-slot recurrence transfers across the
middle-token substitution, consistent with the deliberately shared first and
third tokens dominating a small, uneven family-specific remainder. The
[complete E1 result](EMOJI_FAMILY_EXPLORATORY_RESULTS.md) reports all matrices,
intervals, and negative cells without p-values or a confirmatory label.

## The same emoji is not the same tokenization problem

The next control-design exercise stepped away from activations entirely. A
frozen census sent 115 fixed strings through 14 tokenizer artifacts already
available on mac1, mac2, and furnace, under four exact text contexts. It made no
model forward and opened no target bank.

The 14 artifacts reduced to seven exact output classes on that finite surface.
Only six strings kept the same raw token count across every class. The family
ZWJ sequence ranged from 7 tokens in the most compact classes to 20 in Mistral
v0.3. A leading space changed almost nothing for some tokenizers and changed
the item-span count for 106 of 115 Mistral items and 98 of 115 Qwen items.

Blue circle and blue square exposed the practical limit. The fixed panel had no
single different item that matched both token count and a shared first token
across all seven classes—not in raw text, after a leading space, or before the
fixed prompt. Some byte-style tokenizers provide many color-and-shape matches;
some Gemma shapes are distinct atomic tokens, where a different glyph cannot
share that first token at all.

The lesson is not that controls are impossible. It is that a universal control
panel is the wrong unit. A future cross-tokenizer experiment must freeze a
different feasible control family for each tokenizer structure and say in
advance what replaces prefix matching for atomic-token cases. The [full census
result](MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.md) is descriptive design
evidence, not a new activation result or a paper gate.

## The first frozen cross-model shape axis did not recur at the midpoint

The next study deliberately asked less. It kept the same five-color by
two-shape panel, captured raw-glyph `resid_post` at five formula-selected
depths, and made only the midpoint primary. For each color, it subtracted the
square vector from the circle vector. If those five differences shared one
shape axis, their normalized directions would be parallel. All 120 square-label
permutations supplied the exact null, and the two model cells formed one Holm
family.

The two cells were structurally different by design. Gemma 2 2B 4-bit encoded
all ten glyphs as distinct atomic tokens. OLMo 3 7B BF16 encoded every glyph in
three tokens with a shared prefix. That allowed a feasible declared match in
each tokenizer regime, but it also meant that family, scale, precision,
tokenization, and node changed together.

At the midpoint, Gemma's parallelism was `0.114857969`. Seven of 120 exact
pairings were at least that large, giving raw `p = 0.058333333` and Holm
`p = 0.116666667`. OLMo's parallelism was `0.024628040`, with raw and Holm
`p = 0.275`. Neither cell rejected. The frozen outcome was therefore
`no_dual_model_recurrence`.

Gemma had smaller descriptive p-values at several non-primary depths. They stay
in the public table, but they cannot replace the midpoint after inspection.
OLMo showed a different descriptive pattern: same-color circle-square pairing
became stronger with depth while the common circle-minus-square axis did not.
That contrast is useful for designing a new question, not for naming a color or
shape representation.

Both activation arrays are small enough to publish in full. The OLMo bundle
matched byte-for-byte at mac1, the furnace relay, and mac2; every run and joint
analysis validator passed. The [complete T2 result](MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.md)
is thus a clean negative/mixed observational result. It does not say that shape
geometry is absent or that a 7B model removed it. It says that the exact frozen
midpoint recurrence claim did not clear its two-cell decision rule.

## The five-family grid separated atomic tokens from a shared suffix

T3 used all five public ten-emoji families in an exact 5 × 10 factorial grid.
The slot labels were matched across families, and raw-glyph `resid_post` was
captured at five formula-selected depths. The primary statistic was fixed in
advance: after subtracting each family center, how much of the remaining
activation variation was explained by the shared slot labels, averaged equally
over all five depths? A synchronized 19,999-draw null and a two-model Holm
family supplied the decisions.

The tokenizers created two sharply different cells. Gemma represented all 50
glyphs as 50 distinct atomic tokens. Its all-depth slot fraction was
`0.204304805` against a null mean of `0.199984463`, with Holm `p = 0.208500`.
OLMo represented every glyph as `[shared_prefix, family_token, slot_token]`, so
the same slot reused the exact final token across all five families. Its slot
fraction was `0.500391869` against `0.200184835`, with Holm `p = 0.000100`.
The registered outcome was `olmo_only_token_structured_recurrence`.

The OLMo profile was strongest at the first captured depth and declined from
`0.994722` to `0.295828` across the stack. That is compatible with a shared
input-token identity whose geometry is progressively mixed, but it is not a
mechanistic test of that account. Model family, size, precision, and node also
changed. The [complete T3 result](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.md)
therefore treats the token structure as a sufficient explanation for the OLMo
observation, not as proof of tokenizer causality or emoji semantics.

## One common token later, the OLMo pattern was still there

T3 left one cheap falsification unresolved. Perhaps OLMo's result existed only
because the assay read the exact shared slot token as the current token. T4
moved the readout one position later. Every glyph received either the same
period token or the same newline token, and `resid_post` was measured there.
The raw glyph sequence remained in the immediate prefix, but the current token
was now common to all 50 items within a context.

The two-context, five-depth Gemma statistic was `0.203443011` against a null
mean of `0.200044692`; Holm `p = 0.302950`. OLMo's was `0.537464703` against
`0.199977865`; Holm `p = 0.000100`. The registered outcome was
`olmo_only_common_suffix_carryover`. OLMo was almost unchanged across the two
context summaries: `0.538985382` for a period and `0.535944025` for a newline.

That is a real narrowing of the explanation. The T3 pattern is not confined to
the act of reading the slot token itself. It is already visible at the first
captured block output for the next, common token and then weakens across the
stack. But this does not reveal emoji meaning. A transformer is expected to
mix information from the prefix into the current position. Short-range
propagation of OLMo's explicit `[family_token, slot_token]` structure is still
enough to explain the result.

The [complete T4 result](MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.md)
publishes both arrays and all 20 context-by-depth rows. The clean next question
is distance, not a semantic label: after how many matched carrier tokens does
the layout decay? That question must be frozen separately and cannot replace
the tokenization-matched confirmatory controls.

## Eight matched carrier tokens did not yield the registered decay

T5 froze that distance question before any new model forward. Every glyph was
followed by either eight identical `" a"` tokens or eight identical `" |"`
tokens. The full input stayed unchanged while the readout moved to distances
1, 2, 4, and 8. Gemma 2 2B, Llama 3.2 3B, and OLMo 3 7B each contributed five
fixed depths.

The rule deliberately made a positive result difficult. A model had to show
both matched-slot recurrence at distance 1 and a positive fixed log-distance
attenuation contrast. The larger of those two p-values became the model's raw
p-value, and the three models were Holm-corrected together.

No model passed. Gemma did not establish distance-1 recurrence. Llama and OLMo
did, both at the permutation floor, but Llama's attenuation p-value was `0.188`
and OLMo's was `0.9977`. The registered outcome is
`no_model_distance_attenuation`.

The negative decision is more informative than a post-hoc positive story.
Llama's distance profile was `0.379, 0.414, 0.396, 0.369`; OLMo's was `0.480,
0.519, 0.513, 0.527`. Both remain descriptively elevated at distance 8 rather
than following one simple model-level decay curve. Those tail values are
secondary and do not become new discoveries merely because the primary decay
hypothesis failed.

The full profile adds a useful clue for a future protocol. In Llama and OLMo,
the first captured layer declines with distance, while later depths are flatter
or even rise. That does not prove that later blocks reconstruct a slot variable;
the interaction was not the primary test. It does show why selecting only an
early layer after seeing the result would be misleading. The next clean test
must freeze the interaction itself or break the shared slot structure on the
same artifact.

The [complete T5 result](MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.md) publishes
all three arrays, all 120 carrier-by-distance-by-depth rows, the failed primary
decision, and the three-node transfer evidence. It is observational evidence
about tokenizer-conditioned geometry, not emoji semantics or causal memory.

## Four denser CUDA cells repeated the negative conjunction

T6 kept the full T5 endpoint and changed the model roster and execution cell.
Before any T6 forward, it froze four locally complete BF16
Transformers/CUDA roles: Gemma 2 2B IT, Gemma 3 4B IT, Mistral 7B Instruct
v0.3, and Gemma 3 12B IT. The roster was selected after T5, so this is
prospective only for T6's own unseen outcomes.

Again, no model passed. Gemma 2 2B and both Gemma 3 cells stayed near the
matched null at distance 1. Mistral was different: its distance-1 statistic was
`0.3845` against a null mean near `0.2`, at the `0.00005` permutation floor.
But its attenuation p-value was `0.46975`, so the conjunction still failed.
All four Holm-adjusted IUT p-values were `1.0`. The registered outcome is
`no_dense_model_distance_attenuation`.

This split is more useful than a slogan about larger models. Mistral remained
descriptively high at distance 8 (`0.3930`), while Gemma 3 12B had a nominal
secondary tail p-value of `0.04045`. Neither tail has a multiplicity-authorized
decision. Gemma 3 4B and 12B share the observed tokenizer roster, but one
selected pair does not identify a scale law. The four cells differ in model
family and tokenizer, and all are instruction-tuned, so T6 is neither an
independent confirmation nor a backend-parity experiment.

The operational boundary mattered too. Compute started only after the furnace
was re-observed free and the current `resource:furnace` notice surfaced at a
natural receiver-owned Codex lifecycle boundary. The notification body was not
automatically retrieved, and no reply, commitment, or six-session delivery is
claimed. All 1,600 forwards, four arrays, 160 profile rows, validators, and
return ledgers are in the [complete T6 result](MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.md).

The endpoint has now received enough model breadth for this phase. A cleaner
next step is to freeze a control that breaks shared slot structure on the same
artifact, or to freeze the distance-by-depth interaction itself. Adding more
models without resolving that structure would mostly add more confounding.

## The base checkpoint made the depth interaction visible

T7 took the second of those options. After T6, but before any T7 forward, it
froze one Mistral 7B v0.3 base-model cell and an endpoint that required two
things at once: recurrence at distance 1, and stronger attenuation at the first
captured depth than across the four later depths. The same 50 glyphs, two
carriers, four distances, and five relative depths were retained. No
intervention or generation was added.

This time the conjunction passed. Distance-1 recurrence was `0.377524026`,
against a synchronized slot-permutation null mean of `0.199970302`. The fixed
early-minus-late interaction was `0.149104068`, against a null mean of
`0.000111606`. Both one-sided p-values reached the `0.00005` floor from 19,999
draws. The first captured depth had positive attenuation (`+0.114009450`),
whereas the mean of the four later depths was slightly negative
(`-0.035094618`). Averaging across all five depths would have hidden the split:
that older attenuation statistic was `-0.005273805` with `p = 0.87475`.

The shape is strikingly similar to the already known Instruct profile. Across
the 20 depth-by-distance cells, the descriptive correlation is `0.996785730`
and the MAE is `0.011953404`. That visual agreement is a clue, not an effect
estimate. The endpoint and base checkpoint were chosen after seeing T6, and the
two checkpoints are related. T7 therefore cannot tell us what instruction
tuning changed, cannot serve as independent confirmation, and cannot convert
this observational geometry into a semantic or causal claim.

What it does establish within its narrow frozen scope is that the Mistral
recurrence is not simply flat across depth. It is strongest in an early layer,
then settles into a persistent later-depth profile. A future clean test can now
target that interaction directly while breaking the shared slot structure, or
move to an unrelated checkpoint under a new freeze. The [complete T7
result](MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.md) retains all 40 profile rows,
the compact activation array, the transfer receipt, and the negative claim
boundaries alongside the positive primary outcome.

## A larger model did not pass the engineering gate

E2 asked whether the same MLX route could be qualified for a pinned Llama 3.2
3B BF16 cell before any new scientific result was viewed. Its first frozen
attempt stopped at an MLX BF16-to-NumPy export error. That failure remains part
of the record. V2 added the narrow bridge needed to cast BF16 arrays to FP32 at
the point of NumPy export while keeping model execution in native BF16. This
time, both backend phases completed.

Completion was not qualification. The v2 receipt records
`status: validation_failed` and `scientific_result: false`: 33 of 60 parity checks passed. Tokenization,
within-backend determinism, and exact zero-hook behavior passed. Every
activation-delta subcomparison also passed. But the corresponding logit deltas
failed by a wide margin, the combined delta family passed 0/10, and the frozen
intervention-fidelity check passed 0/10. Its activation NRMSE was about
0.0302–0.0341 against a threshold of 0.01, even though cosine stayed near
0.9994 and the RMS ratio stayed near 1.

MLX was also slower in this recorded cell. Aggregate median latency was
132.127833 ms for Transformers/MPS and 230.138000 ms for MLX, or a recorded
`0.574124367x` speedup. The speed gate failed. This number belongs to the
specific machine, run order, software, model, and timing boundary; it is not a
general verdict on MLX.

The useful result is the gate itself working as intended. It rejected an
engineering route before the study target banks or scientific outcomes were
opened. No Llama emoji-family grid was run, so this is neither a negative emoji
result nor cross-model replication. The [complete E2 result](LLAMA32_3B_MLX_VALIDATION_RESULTS.md)
keeps the activation match, logit mismatch, speed failure, and scientific
boundary together.

A separately frozen Stage-A3 screen then asked whether changing only runtime
compute dtype could produce an eligible route over the same BF16-weight
artifact. FP16 and FP32 both passed identity, determinism, zero-vector, and
within-backend fidelity checks. Speed remained the stopping point. FP16 took
1.9567 times the Transformers/MPS latency on MLX. FP32 was about 1.4% faster,
but the rule required at least 5%. No candidate was selected. Stage A3 did not
run the full cross-backend parity families, so it did not qualify FP32 or
authorize the 50-emoji science grid. The [Stage-A3 result](LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.md)
keeps this engineering no-go separate from any claim about Llama or emoji.

## T8: a large atlas makes the next semantic question testable

T8 used the free furnace window to acquire breadth without spending the future
confirmation set. A zero-forward census divided 1,184 fully-qualified
single-codepoint emoji into 50 prior-exposed calibration items, 842 unseen
discovery items, and 292 deterministic reserve items. The acquired grid crossed
three representations—glyph, official Unicode name, and `U+...` literal—with
two carriers, four readout distances, and nine depths.

The fastest run was not accepted merely because it finished. Batch size 64
completed the grid quickly but failed every one of the 18 fixed batch-one
recapture cases. We kept the thresholds and the failure, then reacquired the
same 892 items with 5,352 batch-one calls. All 28 shards validated, and the
separate 18-case repeat was bit-exact. This makes the batch-one atlas canonical;
the close aggregate profile of the failed batch-64 run does not repair its
vector-level mismatch.

The discovery pattern is strong enough to motivate a real confirmation step.
At layer 31, mean glyph-to-name top-1 retrieval was `0.136580`, compared with
chance `0.001188`, while glyph-to-codepoint retrieval was `0.001188`. The
contrast remained after restricting to 760 glyphs with exactly five tokens and
one common three-token prefix, and in the 43-item stratum with equal glyph/name
token counts. These restrictions were specified after seeing the main result;
they are sensitivity analyses, not confirmation or a fully token-isomorphic
control.

That prospective step is now complete. Before any reserve forward, one global
statistic was frozen: the minimum glyph/name-minus-codepoint top-1 contrast over
all eight layer-31 carrier-distance cells. All 292 reserve items were then
acquired exactly once. The minimum contrast was `0.171233` against a `0.02`
floor, and none of 19,999 common-permutation draws reached it (`p = 0.00005`).
The alignment candidate is therefore confirmed and the T8 reserve question is
closed.

The boundary became sharper rather than broader. One secondary CKA contrast
was slightly negative even though every primary retrieval contrast passed. The
result supports robust correct-name correspondence in this model and layer,
not uniform superiority of every geometry measure, emoji meaning itself, a
causal mechanism, or model generality. The [discovery result](MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1_RESULTS.md)
and [reserve confirmation](MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0_RESULTS.md)
retain both stages and their evidence hashes.

## T10: statistical alignment did not become practical cross-model replication

T10 asked the narrowest useful next question: if the T9 population, views,
carriers, distances, batch rule, and returned final-state endpoint are held
fixed, does the item-name retrieval contrast meet the same statistical and
practical rule across multiple model/tokenizer cells? The model roster and
decision were frozen before any selected-model forward.

The answer split cleanly. All nine model-cell IUTs were statistically
significant, and the four core cells produced a partial-conjunction
`p = 0.0001`. Exact three-view token-count matching retained 281--287 items and
left the minimum contrasts close to their unrestricted values. A token-count
stratum mismatch therefore cannot explain the whole pattern.

But significance was not the entire hypothesis. The practical floor required
at least three of four core cells to have a minimum contrast of `0.02` in both
components. Only Llama 3.2 3B base and Qwen 2.5 7B base did so. OLMo missed in
the unrestricted component and Gemma missed in both. The registered outcome is
therefore `cross_model_replication_not_established_under_frozen_rule`.

That negative primary is more informative than a threshold repaired after the
fact. It says that the direction of the alignment is widespread in this fixed
assay, while its complete-grid magnitude is not yet robust across the frozen
core roster. The monotone Qwen size profile, strong related Mistral-Instruct
cell, and raw-block endpoint differences remain descriptive leads rather than
scale, tuning, or mechanism claims. The [T10 result](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.md)
keeps the statistical/practical split and all nine cells visible.

## T11: decompose the glyph before telling a semantic story

The T10 primary stays negative. A diagnostic replay checked 333 raw shards,
36 activation arrays, and 84,096 scalar values without a mismatch. It also
showed why a single “strong model” is the wrong next move: continuous margins
were positive in all 72 cells, yet item coverage, carrier-distance profiles,
codepoint geometry, and the final-normalization boundary varied substantially
by model. No item was a top-1 hit in all nine models.

T11 therefore changes the unit of analysis rather than repairing T10. It asks
whether a multi-codepoint glyph follows its official whole-sequence name, a
deterministic component label, or a presentation-altered or unfused form. The
fixed systems are presentation selectors, modifiers, ZWJ compositions,
regional flags, keycaps, and a three-item tag-flag microcase, with prior-exposed
single-codepoint anchors for calibration.

Before any T11 forward, 843 acquisition items, 268 reserve items, five views,
token-length-matched wrong-label controls, two carriers, four distances, two
broad endpoints, and a 192-item depth subset were frozen across the same nine
T10 cells. The discovery run then completed all 477 shards: 73,566 forwards and
982,512 FP32 readout vectors, while every reserve item remained unforwarded at
T11 completion.

The first result is broad but bounded. Every required exact target-token-length
control passed. At the returned-final endpoint, the glyph/name margin was
positive in all 72 model-context cells for presentation, modifier, ZWJ, and
regional systems, and in 65/72 keycap cells. But strict first-token matching
left sparse coverage for atomic and presentation systems, item-level rankings
agreed only weakly across models, and only 8/36 ordered Qwen profiles were
strictly increasing. Token length alone does not explain the atlas; that does
not make it tokenizer-independent or a scale law.

The decomposition is not one clean story. ZWJ sequences showed the strongest
narrow presentation-or-fusion pattern: 65/72 cells were positive, no cell had
a strictly negative descriptive interval, and eight of nine model-level
context medians were positive. Regional flags leaned toward both their whole
official names and their component labels. Modifiers and keycaps instead gave
bounded mixed/null contrasts. The useful landing point is therefore a
model-conditioned atlas with a prospective ZWJ T12 candidate—not a verdict
that emoji meaning is compositional or lexicalized. The [complete T11
result](GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.md) keeps those limits alongside
the numbers.

## T12: the reserve refused the attractive story

T12 then did the expensive but clarifying thing. Before any reserve forward it
froze the returned-final endpoint, practical floors, exact-length and
strict-prefix controls, model heterogeneity rules, and a two-hypothesis Holm
family. It opened every ZWJ reserve item (96) and every regional-flag reserve
item (64) once across the same nine model roles and eight contexts. The run
completed 90 shards, 9,792 forwards, and 39,168 FP32 vectors.

Neither registered hypothesis was confirmed. The ZWJ statistic was `0.000369`,
with raw `p = 0.05496` and Holm `p = 0.10992`. Regional presentation/fusion
kept a weak directional trace—eight of nine model summaries were positive and
its component `p` was `0.03538`—but the statistic was only `0.002767`, far below
the frozen `0.02` floor. Regional component tracking was `0.000666`,
`p = 0.12950`, so the required regional conjunction also ended at
`p = 0.12950`. Not one model summary reached any registered practical floor.

That is not a failure of the research program. It is the reserve doing its job.
The strongest T11 contrasts shrank before they could become a semantic story.
An analyzer-independent validator reconstructed all 432 cell medians, reran
the three 49,999-draw tests, and checked every gate with zero mismatches. The
[complete T12 result](GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.md) preserves
the negative cells and the exact claim boundary.

The next question is now better formed: does an emoji-derived intervention do
anything that meaning-matched words, decomposed forms, matched non-emoji
Unicode, rare-token controls, and norm-matched random directions do not? The
[T13 decision map](EMOJI_STEERING_SPECIFICITY_ATLAS_V0.md) keeps that question
open without using T12 to tune its answer.

## T13-EA: separate structured sources from easy-to-move targets

T13-EH finished the furnace-dependent work first: a source bank for all nine
roles and a complete 383,232-row intervention surface for three prespecified
base models. The inputs were the already exposed T11 depth population and all
32 public prestage targets. No protected bank was opened.

The first exact-JS zero gate then failed closed before any nonzero scientific
value was read. We kept that failure as a procedural negative result instead of
quietly relaxing it. A separate v1 amendment was frozen before inspecting the
live residual magnitude. It retained exact equality for every primitive no-op
check and bounded only the derived float32 JS round-trip residual. The amended
gate passed, but that pass is neither an exact-JS claim nor scientific evidence.

The completed point analysis changed the shape of the question. In each pilot
model and sign, glyph-minus-decomposed means were positive for the four
continuous nonnegative endpoints, although this aggregate was driven mainly by
regional flags and keycaps and was weak or reversed for modifiers. Argmax and
the glyph-versus-name and name-versus-decomposed contrasts were less uniform.
Dose ordering was unusually regular, while the largest raw response often
occurred later than the strongest response relative to an isotropic null.
Baseline target margin also predicted argmax fragility in glyph, prototype,
and random conditions. Across all nine source banks, glyph and decomposed
directions were more aligned than glyph and Unicode-name directions, but
wrapper dependence remained substantial.

The coherent interpretation is therefore not “emoji meaning has been found.”
It is a separation problem: how much response comes from structured source
directions, and how much from generic target susceptibility, wrapper context,
and the chosen null? The registered 20,000-replicate cluster bootstrap remains
at 0/20,000, so T13-EA is a completed exploratory point analysis without a
primary significance decision or confirmatory verdict. See the [T13-EA
result](EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.md), [zero-gate
amendment](EMOJI_STEERING_SPECIFICITY_ZERO_GATE_AMENDMENT_V1.md), and [compact
evidence](../artifacts/emoji_steering_specificity_analysis_v0/README.md).

## What we can say—and what we cannot

We can say that, in one pinned GPT-2 FP32 MLX `resid_post` cell, layer 2 retained a positive excess over three prespecified token-count and prefix-panel matched controls under two source-wrapper constructions according to the frozen v1 rule. Layer 4 did not pass that rule.

We cannot call this a tokenization-free glyph effect. We cannot say that GPT-2 has a brown-circle concept, that a particular attention head or MLP implements a glyph feature, that the direction carries human-readable meaning, or that the result generalizes to another model. The independent-source arm reuses the same targets and is not independent model or target replication. The completed secondary diagnostics narrow two token-structure questions descriptively; they do not establish equivalence or remove tokenization from the claim.

The summary boundary remains machine-readable: `causal_claim_authorized` is
`false`. C1 v1 was not passed through an experimental model, tokenizer, or
outcome analysis, but one record was displayed in a research-agent context by
an over-broad read-only search. The complete bank is therefore retired; see
[Holdout status](HOLDOUT_STATUS.md).
E1 does not change either statement and does not establish a semantic,
tokenizer-independent, layer-specific, or robust random-control effect.
T2 adds a bounded cross-model non-recurrence result: neither prespecified
midpoint cell rejected after Holm correction. It does not identify the source
of the heterogeneity or establish that colored-shape geometry is absent.
T3 adds a tokenizer-conditioned split: the OLMo cell with an exact shared final
slot token rejected its frozen omnibus null, while the Gemma atomic-token cell
did not. Because the model cells differ on several axes, this supports a
token-structured alternative without identifying token identity as the cause.
T4 adds one more boundary: the OLMo split persists at a common token one
position later in both fixed contexts. It rejects a strictly current-token-only
description, but not short-range propagation from the structured prefix.
T5 adds a negative duration result: neither Gemma, Llama, nor OLMo passed the
registered conjunction of distance-1 recurrence and positive model-level
attenuation. Llama and OLMo remain descriptively elevated at distance 8, but
the tail and depth interaction are secondary and do not authorize persistence,
semantic, or mechanistic claims.
T6 repeats that negative conjunction in four selected dense CUDA cells. Mistral
retains a strong recurrence component without the fixed attenuation component;
the three Gemma cells do not reject distance 1. This does not establish model
scale, tokenizer equivalence, backend parity, or confirmation.
T7 prospectively tests the Mistral depth interaction in one previously unseen
base checkpoint. Both frozen components reject, but the endpoint and related
checkpoint were selected after T6. The result is neither an instruction-tuning
effect nor independent confirmation and closes no Phase I gate.
T10 adds a claim-matched nine-cell result. Exact token-count matching did not
erase the observed contrast, but only two of four core cells met the frozen
practical floor. It supports three bounded model/tokenizer-cell alignments and
a negative cross-model primary, not tokenization independence, scale, tuning,
semantics, causality, independent replication, or model generality.
T10-D preserves that primary and supplies only diagnostic decomposition. T11
adds a complete exploratory discovery atlas, not confirmatory evidence. T12
then supplies a separately frozen negative confirmation of its ZWJ and
regional candidates. Neither result changes the T10 primary.
T13-EA adds a completed exploratory point decomposition. It does not establish
unique emoji specificity, semantics, behavior, a scale law, or model generality,
and its interval analysis is still pending.

## What comes next

The immediate T13 question is whether structured source directions remain
predictive after generic target susceptibility and null dependence are held
fixed. The next freeze should combine exact token/prefix controls,
leave-one-wrapper-out directions, positive and negative
manifold/covariance-matched nulls, a depth-0.875-versus-1.0 contrast, response
replication in the remaining six source-only roles, and generation endpoints.
The registered 20,000-replicate bootstrap must complete before interval-based
paper wording. Any confirmation still requires a new untouched target bank.

Operational Milestone 2 is complete. Layer 2 can now enter the design of a new
frozen targeted causal protocol; layer 4 remains unresolved and is not a
candidate. This permits protocol design, not a causal claim. Retired C1 v1
cannot serve that experiment. A new versioned causal bank must be prepared
outside the exposed research context and remain untouched through the public
freeze. E1 does not select or modify the layer candidate: any focused
hypothesis derived from E1 also needs its own public protocol and new untouched
target bank.

T2 is complete and should not be rescued by moving its primary layer. Its
five-family option was selected, frozen, and completed separately as T3 rather
than retrofitted onto the T2 decision. T4 then prospectively tested one-token
carryover rather than rescuing a T3 subcell. T5 then froze and rejected the
simple model-level carrier-distance attenuation account. T6 then retained the
same conjunction across four selected dense CUDA cells and again rejected no
model. T7 subsequently froze the depth-by-distance interaction itself and
rejected its one-model IUT in the unseen Mistral base cell. Further adjacent
model breadth is now lower priority. The clean remaining choices are a
same-artifact control that breaks shared slot structure or a genuinely
independent replication of the frozen interaction. Each requires a new
protocol.

T10 is also complete and must not be rescued by lowering its practical floor,
replacing a core model, or promoting an extension cell. T11 remains a clearly
labeled unusual-glyph discovery atlas and cannot revise T10. T12 is complete
and must not be rescued by lowering its floors, selecting a model subset, or
promoting the regional presentation component alone. The clean next step is a
new exploratory specificity design, with any later confirmation using a new
untouched bank outside the exposed research context.

For E2, the research owner selected a separate Transformers/MPS-only scientific
route. V1 failed its tokenizer preflight before model-weight loading or any
forward because the audit conflated raw and contextual wrapper tokenization; it
has no scientific outcome. The literal 50-emoji arm and independently centered
35-emoji token-structural sensitivity arm are now rebound before outcome access
in the corrected [v2 MPS transport
protocol](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.md). This does not turn the MLX
no-go into a pass, and the failed MLX v2 and Stage-A3 thresholds remain
unchanged.

T14-C met the closed-bank requirement by freezing the candidate operation,
endpoint, controls, site roster, selector, and multiplicity family before its
new bank was materialized. Any future versioned causal bank must follow the
same boundary. Independent backend and model or tokenizer replication remain
open. Final-paper wording and any supporting replication must prospectively
bind scientific roles to frozen inputs and account for data-dependent
prototype resampling.

Phase I still ends with an English paper, whether the final pattern is positive, mixed, or negative. That paper must show layer 2 and layer 4 together, distinguish frozen-v1 inference from post-hoc sensitivity, report the completed diagnostics, T2 non-recurrence, the T3 tokenizer-conditioned split, and T4 one-token carryover with their claim boundaries, and connect every statement to a sealed artifact. The first map has become sharper. It has also become harder to overread, which is exactly what the controls were for.
T5's failed attenuation endpoint and its complete persistent descriptive
profiles belong in that record as well; neither may be replaced by a favorable
distance, carrier, or depth.
T6's four non-rejections, Mistral component split, and all 160 profile rows also
belong in that record without promotion of a tail, depth, or model pair.
T7's positive depth interaction and all 40 rows belong beside them, with its
post-T6 model selection and non-confirmatory status stated explicitly.
T8/T9's positive single-model reserve confirmation and T10's negative
cross-model primary must also appear together. The paper should state that
token-count matching retained the signal, while only two core cells cleared
the practical floor and no tokenizer-independent or model-general claim was
authorized.
T10-D's heterogeneous diagnostics, T11's exploratory status, and T12's
completed negative confirmation must remain explicit. T12 must be presented as
a separately frozen result rather than folded back into T11 or rescued by a
new endpoint.

## The larger grid found a regime, then the causal test removed the easy story

T14-X asked the broad operational question with enough breadth to expose its
sign. Across six base-model roles and two late depths, all 12 headline JS
intervals excluded zero. Nine were positive and three were negative. The Qwen
sequence was not monotone with size: positive at 0.5B, split by depth at 1.5B,
negative at 3B, and positive again at 7B. That is a real regularity in the
frozen grid, but it is a response-anisotropy regime, not a scale curve and not
evidence that emoji directions are universally stronger.

The source-form analysis made the boundary sharper. Some modifier and ZWJ
contrasts favored the glyph surface, while keycap and many other contrasts did
not. Null family and intervention sign also changed the result. The more data
we collected, the less defensible a single glyph-privilege story became.

T14-C then asked whether one downstream Llama component carried the operational
effect. Its selector chose `mlp_out` block 24 before the new target bank was
created. On 192 untouched targets, the treatment contrast was positive but
below its practical floor, necessity was stably negative, and sufficiency was
far below its floor. Every no-op, restoration, positive-control, and sham gate
passed. The failure therefore belongs to the scientific hypothesis, not to the
hook.

That is a useful close. One selected component is not supported as the
necessary and sufficient mediator. We will not choose the runner-up or lower a
floor. A distributed or redundant route is now a plausible future question,
but first the paper should preserve this exact sequence: broad signed regime,
prospective localization, untouched confirmation, negative causal IUT.

## The incongruent pairs were not simply louder—they bent the output in a shared shape

T15-A returned to a more semantic-looking question, but kept the measurement
deliberately operational. Each axis paired two emoji with two words: fire and
snow with “hot” and “cold,” for example. Because every emoji and every word
appeared once on each side of the contrast, their individual main effects
cancelled. What remained was the interaction between the pairings chosen by
the experimenter.

Across four base models, two late depths, and both signs, the result was
strikingly consistent in one particular sense. For every one of the 16 primary
cells, the true within-axis interactions produced more similar vocabulary-wide
response patterns across axes than the same checkerboard construction made
from mismatched axes. The intervals were entirely positive in all 16 cells.

The tempting story would be that incongruent pairs simply push the model
harder. The other measurements refused that story. Response energy changed
direction across models and signs. Word-main and emoji-main effects traded
places. Source order mattered in some cells and reversed in others. Individual
pair residuals did not show a common positive incongruence excess. The shared
feature was the *shape* of the response, not its overall volume.

That distinction is the most interesting outcome. It gives us a concrete
candidate for a later causal intervention on an interaction-residual subspace,
while leaving the large semantic claim untouched. These are labels supplied by
the experiment; the experiment does not show that a model notices a
contradiction as a person would. The next clean test must change the axes,
targets, and model or backend, then freeze removal, addition, and restoration
before looking. The [complete T15-A result](EMOJI_WORD_INCONGRUENCE_INTERACTION_V0_RESULTS.md)
also records the post-open one-line analyzer repair and every negative or
heterogeneous family that keeps this candidate honest.
