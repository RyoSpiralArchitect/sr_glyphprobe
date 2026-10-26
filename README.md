# GlyphProbe

[日本語](README.ja.md)

## Published preprint and current research

[Published PDF](output/pdf/glyphprobe_preprint_20261015.pdf) ·
[DOI: 10.5281/zenodo.23376699](https://doi.org/10.5281/zenodo.23376699) ·
[Paper source and build](paper/README.md) ·
[Current claims](paper/CURRENT_CLAIMS_20261015.md) ·
[Next-paper theme](docs/PAPER_NEXT_THEME_20261026.md) ·
[October 26 integration scope](docs/PUBLIC_INTEGRATION_SCOPE_20261026.md)

**Beyond Short Names: Emoji Keyword Retrieval across Models and Bounded Causal
Tests**, version 1.0.0, was published as an independent preprint on October 15,
2026. It separates cross-model lexical readability, bounded causal tests and
the limits of contextual response measurement. It was revised following
reviewer feedback from the NeurIPS 2026 workshop **Interpretability as a Science
(InterpScience)**; it is not an accepted workshop or proceedings paper.

The published negative results remain part of the contribution. The tested
rank-8 accounts were unsupported or uncalibratable, and the conditional
attention-path margin result had zero mean absolute top-1 effects. Explicit-report
qualification returned 88/96 correct direct/minimal answers and 104/192 correct
A/B answers; both prespecified requirements failed. CLDR correspondence is a
lexical measurement, not a human-semantic label or the ultimate research goal.

The original [sr_glyphprobe repository](https://github.com/RyoSpiralArchitect/sr_glyphprobe)
is now **public**, as is the curated October 15
[sr_glyphprobe-public release](https://github.com/RyoSpiralArchitect/sr_glyphprobe-public).
The October 26 integration brings selected research material into this original
repository; it does not import the unpublished development history wholesale.
Individual human records, protected holdouts, operational handoffs and raw
machine-specific runtime records are excluded from this integration. Selected
scientific files are not a complete-run replay bundle. The
[scope note](docs/PUBLIC_INTEGRATION_SCOPE_20261026.md) records these boundaries;
it does not certify all prior repository history.

The published PDF is unchanged, with SHA-256
`9f9a34b578b8eeec6dd8f08994fa348ea050d5477c3387663cc885d9cd30d673`.
Its 36 pages, 231 passing targeted tests, and absence of overfull boxes or
undefined references are **October 15 validation records**, not a claim that
231 tests were rerun during this integration. The exact-PDF
[public validation receipt](artifacts/public_release_20261015/evidence/document_validation.public.json)
preserves that historical evidence.

### Verify the published saved-score package

The [published archive](output/artifacts/glyphprobe_public_release_20261015_v2.zip)
has SHA-256 `36959018915a13b988d83b7db13b9e3bb91b6e3a660649cbc8a270340b68f409`.
Its unchanged contents are also available under
[`artifacts/public_release_20261015/`](artifacts/public_release_20261015/README.md).
From this repository root, using Python's standard library only:

```bash
python3 -B artifacts/public_release_20261015/paper/scripts/build_public_release_20261015.py \
  verify artifacts/public_release_20261015
```

This verifies the exact package and replays all 4,640 saved qualification scores
with two arithmetic implementations. It does not reacquire model logits,
validate human meaning, or establish publication. Its deliberate
`publication_verified: false` reports that limited scope; DOI publication is
documented separately. The package's preparation manifests stay unchanged.
The [license guide](paper/PUBLIC_LICENSES_20261015.md) assigns CC BY 4.0 to the
author-owned paper, original paper figures and newly released public data;
code and ordinary project documentation retain Apache 2.0, with third-party
notices preserved.

### Next-paper direction — proposed, not a new result

[From readable symbols to causal use](docs/PAPER_NEXT_THEME_20261026.md) asks how
local K/V changes propagate through later computation, and how that propagation
can be distinguished from nonlinear readout effects. T22 currently supplies
descriptive evidence from eight previously exposed items. Local V-only attention
invariance is true by construction; later attention changes were observed, but
their mediation of the lexical effect has not been identified. The fixed
384-item exploration remains unrun and is not fresh confirmation. The theme
note changes no protocol and authorizes no experiment.

[Paper 2 discussion notes](docs/PAPER2_DISCUSSION_NOTES_V0.md) · [T22 exposed-eight K/V results](docs/T22_CPU_LEXICAL_RESULTS_V0.md) · [Frozen 384-item design](docs/T22_KV_EXPLORATION_CPU_V0.md): retrospective framing, descriptive CPU evidence, and portable numerical replay. The 384-item exploration remains unrun; its reduced runner still requires implementation and validation.

## Historical study index

The following studies, page counts and receipts belong to their named historical
versions. They do not describe the current published PDF or imply that every
historical raw input is included in this public checkout.

[September post-review evidence audit](docs/POST_REVIEW_EVIDENCE_RESULTS_V0.md): T19
model-free statistical replay, T20 checkpoint selection, and descriptive T21
own-keyword/competitor decomposition. The scientific decisions are unchanged.
[Historical package checks](validation/post_review_evidence_v0/submission_qa.json)
record the 9-page main text, compact replay, figure regeneration, and regression tests.

[T21 conditional path result](docs/T21_GLYPH_CONTEXT_PATH_RESULTS_V0.md) · [T21 prospective design](docs/T21_GLYPH_CONTEXT_PATH_CONFIRMATION_V0.md)

[Phase I first-draft PDF](output/pdf/glyphprobe_t19_first_draft.pdf) · [Paper source and build](paper/README.md) · [T20 frozen protocol](docs/T20_LEXICAL_ALIAS_OPTIMIZED_SUBSPACE_CAUSAL_V0.md) · [T19 lexical + causal result](docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0_RESULTS.md) · [T19 paper story](docs/PAPER_STORY_T19_LEXICAL_NEIGHBORHOOD_V0.md) · [T19 frozen protocol](docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.md) · [T18 fresh lexical result](docs/FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0_RESULTS.md) · [T18 paper story](docs/PAPER_STORY_T18_FRESH_LEXICAL_V0.md) · [T18 frozen protocol](docs/FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0.md) · [T17 depth-atlas result](docs/GLYPH_NAME_DEPTH_TRAJECTORY_V0_RESULTS.md) · [T16 paper story](docs/PAPER_STORY_T16_V0.md) · [T16 operational behavior and causal result](docs/T16_OPERATIONAL_SEMANTICS_CAUSAL_SUBSPACE_V0_RESULTS.md) · [T16 distributed late-band result](docs/T16_DISTRIBUTED_LATE_BAND_V0_RESULTS.md) · [T16 exact-UTF mixing result](docs/T16_UTF_IDENTITY_MIXING_V0_RESULTS.md) · [T16-UTF-X1 scale and order stress test](docs/T16_UTF_SCALE_VARIANTS_V1_RESULTS.md)

[日本語](README.ja.md) · [T15-B prospective replication result](docs/EMOJI_WORD_INCONGRUENCE_REPLICATION_V0_RESULTS.md) · [T15-B protocol](docs/EMOJI_WORD_INCONGRUENCE_REPLICATION_V0.md) · [T15-A emoji × word result](docs/EMOJI_WORD_INCONGRUENCE_INTERACTION_V0_RESULTS.md) · [T15-A protocol](docs/EMOJI_WORD_INCONGRUENCE_INTERACTION_V0.md) · [T14-X / T14-C result](docs/EMOJI_STEERING_T14_X_T14_C_RESULTS_V0.md) · [T13-EA bootstrap execution freeze](docs/EMOJI_STEERING_SPECIFICITY_BOOTSTRAP_EXECUTION_V1.md) · [T13-EA exploratory point result](docs/EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.md) · [T13-EA zero-gate amendment](docs/EMOJI_STEERING_SPECIFICITY_ZERO_GATE_AMENDMENT_V1.md) · [T13-EH acquisition protocol](docs/EMOJI_STEERING_SPECIFICITY_HARVEST_V0.md) · [T12 reserve result](docs/GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.md) · [T13 question map](docs/EMOJI_STEERING_SPECIFICITY_ATLAS_V0.md) · [T11 exploratory result](docs/GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.md) · [T11 frozen protocol](docs/GLYPH_SYSTEM_DECOMPOSITION_V0.md) · [T10 diagnostics](docs/SEMANTIC_ATLAS_CROSS_MODEL_DIAGNOSTICS_V1.md) · [T10 cross-model result](docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.md) · [Mistral base depth-distance results](docs/MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.md) · [Dense CUDA results](docs/MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.md) · [Carrier-distance results](docs/MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.md) · [Carrier-distance protocol](docs/MULTIFAMILY_CARRIER_DISTANCE_V0.md) · [Common-suffix results](docs/MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.md) · [Matched-slot results](docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.md) · [Multifamily geometry results](docs/MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.md) · [Tokenizer census results](docs/MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.md) · [E2 MPS transport v2 protocol](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.md) · [v1 preflight failure](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.md) · [Holdout status](docs/HOLDOUT_STATUS.md) · [E2 Stage-A3 numeric-screen result](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.md) · [E2 Stage-A v2 result](docs/LLAMA32_3B_MLX_VALIDATION_RESULTS.md) · [E1 exploratory results](docs/EMOJI_FAMILY_EXPLORATORY_RESULTS.md) · [Milestone 2 results](docs/MILESTONE2_RESULTS.md) · [Baseline results](docs/RESULTS_V1.md) · [Roadmap](docs/ROADMAP.md) · [Phase I paper plan](docs/PAPER_OUTLINE.md)

GlyphProbe is an auditable research harness for one deliberately narrow question:

> When source construction, intervention magnitude, clipping, prompts, and random controls are fixed, do different emoji- or glyph-derived activation directions leave reproducible, direction-specific fingerprints in a language model's next-token distribution?

The default panel is a balanced `5 colors × 2 shapes` grid:

```text
🟤 🟫   🟠 🟧   🟢 🟩   🔵 🟦   🟣 🟪
```

GlyphProbe starts with blind numerical screening. A reproducible fingerprint motivates a targeted causal test. Later studies below separately test lexical retrieval, component mediation, and a conditional attention-path contribution; none establishes human meaning or a complete circuit.

## Historical evidence snapshot

The first standard MLX cell uses the pinned `openai-community/gpt2` revision `607a30d783dfa663caf39e06633721c8d4cfcd7e`, FP32, and full-sequence `resid_post` addition at layers 2, 4, 7, and 9.

| Check | Current result | Scope |
|---|---:|---|
| Transformers/MPS ↔ MLX parity | 80/80 gates passed | 4 prompt lengths × 4 standard layers; tokenizer, baseline activation/logit, zero-hook, and fixed-intervention checks |
| Synchronized end-to-end median latency | 17.52 ms → 10.73 ms | 1.63× in the recorded environment; tokenization, capture/intervention, evaluation, and NumPy transfer included |
| Standard MLX intervention records | 14,208; 0 errors | 10 glyphs, 24 target prompts, 3 direction seeds, 3 strengths, 4 layers |
| Readiness gates | 11/11 | pre-causal readiness only |
| Median held-out fingerprint advantage | 0.608 | 25/36 layer–seed–strength cells were positive; 11/36 were not |
| Median cross-seed fingerprint advantage | 0.931 | seeds are repeated direction estimates, not independent observations |
| Milestone 2, primary-source layer 2 | +0.208363, 95% CI [0.137463, 0.276893] | Holm-adjusted p = 0.00143999; robust to the prespecified matched controls under frozen v1 |
| Milestone 2, primary-source layer 4 | -0.0329465, 95% CI [-0.0761085, 0.0110094] | Holm-adjusted p = 0.999500; unresolved under frozen v1 |
| Milestone 2, independent-source layer 2 | +0.187507, 95% CI [0.125489, 0.247659] | Holm-adjusted p = 0.00393996; robust to the prespecified matched controls under frozen v1 |
| Milestone 2, independent-source layer 4 | -0.086379, 95% CI [-0.159246, -0.016917] | Holm-adjusted p = 0.999430; unresolved under frozen v1 |
| E1 global specificity, layer 2 | 0.014752595564, 95% descriptive interval [0.002875238085, 0.027439243404] | exploratory; all five family-specific intervals included zero |
| E1 global specificity, layer 4 | 0.014887989201, 95% descriptive interval [0.003407563347, 0.019684351979] | intended negative comparator was not negative; all five family-specific intervals included zero |
| Multifamily tokenizer census | 14/14 roster entries; 7 exact output classes | tokenizer-only; no universal equal-count plus first-prefix candidate for blue circle or blue square in the fixed 115-item panel |
| Multifamily colored-shape geometry v0 | `no_dual_model_recurrence` | Gemma midpoint T = 0.114858, Holm p = 0.116667; OLMo midpoint T = 0.024628, Holm p = 0.275; both non-rejecting |
| Multifamily matched-slot geometry v0 | `olmo_only_token_structured_recurrence` | Gemma all-depth T = 0.204305, Holm p = 0.2085; OLMo T = 0.500392, Holm p = 0.0001; shared final slot token remains sufficient |
| Multifamily common-suffix carryover v0 | `olmo_only_common_suffix_carryover` | Gemma two-context T = 0.203443, Holm p = 0.30295; OLMo T = 0.537465, Holm p = 0.0001; recurrence remains one common token later |
| Multifamily carrier-distance v0 | `no_model_distance_attenuation` | Gemma IUT/Holm p = 1.0; Llama = 0.564; OLMo = 1.0; Llama and OLMo recur at distance 1 but do not pass the fixed attenuation component |
| Multifamily dense CUDA carrier-distance v0 | `no_dense_model_distance_attenuation` | Four-model Holm family: no rejection; Mistral distance-1 raw p = 0.00005 but attenuation p = 0.46975 |
| Mistral 7B base depth-by-distance v0 | `recurrence_and_early_depth_attenuation_excess` | Fixed recurrence and early-minus-late components both raw p = 0.00005; selected post-T6 base cell, not independent confirmation |
| T11 matched glyph/name atlas | positive median margin in all 72 returned-final cells for presentation, modifier, ZWJ, and regional systems | exploratory; exact target-token-length controls passed, but strict first-token coverage was sparse for some systems |
| T11 decomposition atlas | ZWJ fusion contrast positive in 65/72 returned-final cells | exploratory discovery candidate; cross-model agreement was weak |
| T12 ZWJ reserve confirmation | statistic 0.000369; raw p = 0.05496; Holm p = 0.10992 | not confirmed; 0/9 models reached the frozen 0.005 practical floor |
| T12 regional dual reserve confirmation | presentation p = 0.03538, component p = 0.12950; IUT/Holm p = 0.12950 | not confirmed; both regional statistics were below the frozen 0.02 floors |
| T13-EH specificity harvest | 9-role source bank plus a fixed 3-role, 383,232-row intervention surface | exploratory acquisition only; no primary hypothesis, protected bank, or confirmatory verdict |
| T13-EA specificity analysis | F1–F6 exploratory point analysis complete; bootstrap execution v1 frozen | The post-outcome implementation roster has 600 complete high-level estimands in 100 fixed chunks; production remains at 0/20,000 and there is no confirmatory verdict |
| T14-X signed response regime | 559,488 rows across 6 base models and 2 late depths | all 12 JS intervals excluded zero: 9 positive, 3 negative; exploratory, non-monotonic, and not a scale law |
| T14-C selected-site causal test | `mlp_out` block 24; 192 untouched targets; 15,360 records | engineering controls passed; treatment, necessity, and sufficiency IUT non-rejecting; causal claim remains unauthorized |
| T15-A emoji × word interaction fingerprint | 393,472 rows across 4 base models, 8 axes, and 2 late depths | all 16 primary model × depth × sign response-coherence intervals were positive; energy, main-effect, order, depth, and dose families remained heterogeneous |
| T15-B prospective holdout replication | 491,712 rows across 2 new models, 8 new axes, and 48 new targets | frozen R1 gate supported in both models: SmolLM2 +0.020422 [0.012887, 0.031510], Mistral +0.060397 [0.056621, 0.062194]; 6/8 separate primary-dose cells positive and 2 mixed |
| T16 operational behavior | 768 rows across 2 instruction-tuned models and 8 new axes | all four meaning-choice/congruence gates passed; accuracy 0.754–0.953; supports only frozen forced-choice association and congruence |
| T16 T15-B residual-subspace causality | 5,376 Mistral rows; zero and restoration gates passed | gate not supported: treatment -0.148438, sufficiency -0.085938, necessity -0.054688; the registered direction moved the explicit mismatch endpoint oppositely |
| T16 distributed late band | 15,360 Llama rows; 8 joint sites over blocks 24–27 | joint IUT non-rejecting; necessity +0.000871 passed, sufficiency -0.000146 failed, and treatment +0.001717 missed its 0.002 floor |
| T16 exact-UTF identity and mixing | 2,880 records, 2 models, 6 construction families, 4 depths, n=1/2/4/8/16 | exploratory: n=1 was exactly identical; cross-minus-within displacement intervals were positive in 8/8 cells, conditional on recorded tokenizer paths |
| T16-UTF-X1 scale and sequence variants | 515,808 records, 9 fixed model/tokenizer cells, 4 depths, n=1…500 | exploratory: primary and n=500 cross-minus-within were positive in 36/36 cells; exact-token-multiset order controls made blocked runs largest in 72/72 cells; not a scale law or tokenizer-independent Unicode result |
| T17 raw emoji → Unicode-name depth atlas | 292 prior-exposed items, 9 exact cells, 9 depths, 567,648 readouts | exploratory: name-minus-codepoint top-1 was positive in 9/9 models from depth 0.375; peaks were heterogeneous, and final paired margins were positive in 9/9 while final CKA contrasts were positive in 4/9 |
| T18 fresh composite-glyph confirmation | 192 exact-surface-fresh items, 9 fixed cells, 13,824 forwards, 497,664 readouts | frozen `r=3/4` core primary passed at p=0.0001; 4/4 core and 8/9 total cells passed both unrestricted and token-count-matched practical rules |
| T19-L alias × Unicode-symbol control | 110 observational items, 9 fixed cells, 7,920 forwards, 285,120 readouts | frozen `r=3/4` core primary passed at p=0.0027; 4/4 core and 9/9 total cells passed unrestricted and exact four-view token-count-matched rules |
| T19-C component causality | 128 source and 192 untouched evaluation emoji; 256 + 2,880 forwards; 8,064 intervention rows | 6/6 engineering gates exact; neither primary block-24 `attn_out` nor `mlp_out` was jointly necessary and sufficient; post-hoc full-interchange ceilings at those sites were 0.0000/+0.0052 |
| T20-C optimized-subspace causality | 128 source + 384 fresh evaluation emoji in 4 contexts; 384 + 32,256 forwards; 33,048 training passes; 124,416 intervention rows | registered verdict: both primary residual sites uncalibratable (sufficiency ceilings +0.0234/+0.0254 < 0.06); full-interchange asymmetry motivates a separate glyph-context path test |
| T21-C conditional glyph-context path | 384-item exposed pilot followed by all 195 remaining T19/T20-unused emoji; one Llama 3.2 3B configuration | all five prespecified one-sided simultaneous 95% lower bounds are positive for the continuous margin; absolute necessity and rescue top-1 mean effects are both zero |
| E2 Llama 3.2 3B BF16 parity | 33/60 gates passed | Stage-A v2 engineering validation failed; no scientific E2 grid was run |
| E2 machine-local median latency | 132.127833 ms → 230.138000 ms | Transformers/MPS → MLX; speed gate failed; recorded MLX speedup 0.574124367x |
| E2 Stage-A3 runtime-dtype selection | no candidate selected | FP16 and FP32 passed identity, token/determinism, zero-vector, and fidelity gates; both failed only speed |
| E2 Stage-A3 FP16 median latency | 165.0765625 ms → 322.9998125 ms | MLX/MPS fraction 1.956666698; all 10 MLX cell medians were slower |
| E2 Stage-A3 FP32 median latency | 465.013771 ms → 458.619459 ms | MLX/MPS fraction 0.986249198; approximately 1.375% lower, short of the required 5%; 4/10 MLX cell medians were slower |

The baseline fingerprint rows are descriptive outputs of one pinned model cell;
the Milestone 2 rows are frozen-v1 target-cluster results with the qualifications
summarized below. The [parity receipt](validation/mlx_gpt2_parity/receipt.json)
is explicitly marked as an engineering validation rather than a scientific
result. The [standard-run audit](validation/run_audits/colored-shapes-v1-standard-mlx--c493ae1e18743922.json)
passed 15/15 integrity checks with caveats. That baseline's `causal_claim_authorized`
remains `false`. See [Results v1](docs/RESULTS_V1.md) for its qualification and
negative cells.

Latency is machine-, load-, and software-dependent. Treat the receipt as the measurement, not 1.63× as a universal MLX claim.

### T21 conditional glyph-context path

After a 384-item exposed pilot, the block-21 candidate, five-contrast family,
20,000-replicate simultaneous inference, and stopping rule were specified
before model evaluation of all 195 remaining T19/T20-unused emoji. Under a
codepoint-state readout reset, replacing or restoring glyph-position keys and
values in strictly later attention blocks changes a continuous alias-retrieval
margin. Both absolute and suffix-position-adjusted necessity and rescue
contrasts, together with full-prefix calibration, have positive simultaneous
95% lower bounds. The adjusted effects are `+0.002326` and `+0.002267`.

This is a conditional directional contribution in one model and a fixed
source/gallery setting. Absolute necessity and rescue top-1 mean effects are
both zero; generated behavior, emoji specificity, and a complete or
unconditional mediator remain untested. The T19/T20 verdicts are unchanged.
All 195 reserve items are now used; another prospective test needs a new
population. The [result report](docs/T21_GLYPH_CONTEXT_PATH_RESULTS_V0.md)
includes the numerical reconstruction and a NumPy-only statistical replay.

### T19 lexical breadth and component-causal status

T19-L crossed 55 atomic emoji and 55 non-emoji Unicode symbols with canonical
labels, lexically disjoint aliases, and literal codepoints. Across all nine
frozen model/tokenizer cells, emoji alias-minus-codepoint retrieval was
positive in both unrestricted and exact four-view token-count-matched
analysis. All four core cells passed the registered partial-conjunction primary
(`p = 0.0027`), and all 9/9 cells passed their model IUT and `0.02` practical
floors. Symbol alias effects were smaller and heterogeneous; emoji-minus-symbol
point estimates were positive in 9/9 cells, but this comparison was registered
secondary.

The admitted T19-C follow-up learned rank-8 glyph–alias subspaces from 128
source emoji and tested them on 192 untouched emoji in Llama 3.2 3B. All six
zero-hook and restoration checks were exact, but neither primary block-24
`attn_out` nor `mlp_out` site passed the necessity–sufficiency intersection.
The result supports a token-count-matched CLDR lexical correspondence while
this simple late-component mediator fails its joint criterion—establishing
neither rendered perception, synonym understanding, a universal manifold, nor
a complete circuit. See the
[full result](docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0_RESULTS.md), [paper
story](docs/PAPER_STORY_T19_LEXICAL_NEIGHBORHOOD_V0.md), and [frozen
protocol](docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.md).

### T20 calibrated optimized-subspace causal status

T20-C was specified and authorized after the T19-C analysis was validated.
It tested interchange-optimized rank-8 subspaces at three residual-stream and
six component sites, using 384 atomic emoji unused in T19/T20 and four
contexts. Full-state swaps served as registered positive controls. Both
primary residual sites returned *uncalibratable at this endpoint*
(sufficiency effects `+0.0234`/`+0.0254`, below the registered `0.06`
calibration minimum). Block-27 residual swaps reproduce both baseline
retrieval rates, whose gap is `0.0332`. At blocks 21/24, injection transfers
71–76% of that gap and replacement in the glyph forward removes 4–25%.
This asymmetry motivates direct tests of recovery from unchanged
glyph-position context; it does not identify that pathway or exclude every
rank. Optimized subspaces fit source items (residual-site training InfoNCE
0.52–1.26), with held-out source validation at 0–1 item. Limited data and
optimization remain alternative explanations for weak generalization.
Descriptive post-hoc full-state swaps at the T19-C primary sites produced
near-zero sufficiency effects, limiting the interpretation of that earlier
negative without changing its registered decision. See the
[frozen protocol](docs/T20_LEXICAL_ALIAS_OPTIMIZED_SUBSPACE_CAUSAL_V0.md) and
the committed results under
`validation/t20_lexical_alias_optimized_subspace_causal_v0/results/`.

### T18 fresh composite-glyph confirmation status

T18 prospectively tested whether a raw Unicode sequence retrieves its English
Emoji short name better than its literal `U+...` spelling. Its 192
multi-codepoint sequences were absent as exact UTF-8 surfaces from the complete
frozen repository tree and outside the complete T11 selection. The panel,
nine model/tokenizer cells, late-depth window, token-count strata,
multiplicity, and practical floor were pushed before acquisition.

All 54 shards completed: 13,824 forwards and 497,664 readouts. The registered
`r = 3 of 4` core partial-conjunction primary passed at `p = 0.0001`; all four
core cells passed both unrestricted and token-count-matched tests and the
`0.02` practical floor. Eight of nine total cells passed the same bounded
rule. Japanese matched point estimates were positive in 9/9 as a non-rescuing
secondary result. Paired margins were positive in 9/9, while matched CKA was
positive in only 3/9 and only 8/192 items were positive in every core cell.
The bounded reading is fresh-surface, item-specific lexical binding with
model-private implementation—not pretraining holdout, rendered-glyph
perception, meaning, a shared mechanism, or a scale law. See the [complete
result](docs/FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0_RESULTS.md),
[candidate paper story](docs/PAPER_STORY_T18_FRESH_LEXICAL_V0.md), and
[frozen protocol](docs/FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0.md).

### T17 glyph–name depth-atlas status

T17 returns to the raw emoji surface by comparing each of 292 items with its
official Unicode name and literal codepoint identifier across nine exact
model/tokenizer cells and nine normalized depths. All nine models had a
positive equal-context name-minus-codepoint top-1 estimate from depth `0.375`
through the returned final state. Exact token-count-matched estimates were
positive in all nine from `0.25` onward. The paths were not shared: two models
peaked at the first block, one at `0.125`, one at `0.75`, and five at `0.875`.

At the final state, paired item margins favored names in 9/9 models, but global
centered-linear-CKA contrasts did so in only 4/9. The bounded contribution is
therefore item-specific lexical correspondence with heterogeneous onset, not
a universal late phase transition or a globally aligned semantic manifold.
The population was already exposed in T9/T10, so the atlas is exploratory.
See the [full result](docs/GLYPH_NAME_DEPTH_TRAJECTORY_V0_RESULTS.md) and the
[candidate paper story](docs/PAPER_STORY_T17_GLYPH_NAME_V0.md).

### Milestone 2 status

Milestone 2 preflight passed and the frozen 48-target P2 bank was opened once.
The frozen v1 result is mixed: layer 2 exceeded the three prespecified
token-count and prefix-panel controls in the primary-source arm (+0.208363,
95% CI [0.137463, 0.276893], Holm p = 0.00143999) and in the independent-source
arm (+0.187507, [0.125489, 0.247659], Holm p = 0.00393996). Layer 4 was
unresolved in both arms (-0.0329465 and -0.086379, respectively).

These controls match the three-token count and panel-level 9:1 prefix structure,
not token identity. Panel C contains one declared semantic-near control, `🟥`.
The source-robustness arm reuses the same P2 targets and is not an independent
target or model replication. A separate input-binding audit passed, while a
post-hoc sensitivity analysis showed that rebuilding leave-one-group-out
prototypes inside each target-bootstrap replicate widens the intervals. It does
not overwrite the frozen v1 statuses. Both secondary diagnostics then completed
their 14,208-row grids with zero errors, zero-hook activation/logit RMS of 0, and readiness 11/11.
Their random-adjusted headline advantages were +0.751225 (suffix-matched) and
+0.601038 (prefix-homogeneous). These are not the raw separation scores used in
the paired diagnostic comparison. At 96 dimensions, the descriptive
standard-minus-diagnostic median was +0.002624 for suffix matching (20/36 cells
positive) and +0.022096 for prefix homogenization (25/36 positive). These
post-hoc diagnostics are not inferential or equivalence tests. C1 v1 was not
used by those experiments, but it is now retired after the separately recorded
research-context exposure described in [Holdout status](docs/HOLDOUT_STATUS.md).

For runtime provenance, the first matched-null A process was externally
interrupted after 798 rows under severe machine load. A sealed resume completed
the exact 14,208-row grid without duplicates, missing rows, or errors, with
zero-hook activation/logit RMS still at 0. The event is not model evidence or a general speed claim.

See [Milestone 2 results](docs/MILESTONE2_RESULTS.md) for the exact results,
analysis limitations, sensitivity intervals, and evidence links. The result is
pre-causal and does not establish semantics, mechanism, a circuit, or a
tokenization-free glyph effect.

### E1 exploratory status

The frozen token-isomorphic emoji-family screen is complete across five ten-glyph
families. Its full matched-slot transfer matrix was broadly positive at both
layers: the 25 family-pair means ranged from 0.395455 to 0.484915 at layer 2 and
from 0.602564 to 0.681909 at layer 4. The much smaller global within-family
excess was 0.014752595564 at layer 2 and 0.014887989201 at layer 4. Every one of
the ten family-specific descriptive intervals included zero.

This pattern suggests that transfer tied to the deliberately shared first and
third GPT-2 tokens dominates the small family-specific excess. It does not
support a semantic-family, tokenizer-independent, layer-specific, or causal
claim. Random-control comparison was also heterogeneous: 10/30 prespecified
family × layer × seed cells were non-positive, comprising all five families at
layer 2 seed 307 and all five at layer 4 seed 101. All 8,880 intervention rows
completed with zero errors and exact zero-hook activation/logit RMS of 0.

E1 used the already explored 24-target prestage bank. It did not open P2 or C1,
does not change the Milestone 2 classification, and does not satisfy a Phase I
paper gate. See the [E1 results](docs/EMOJI_FAMILY_EXPLORATORY_RESULTS.md),
[frozen protocol](docs/EMOJI_FAMILY_EXPLORATORY_PROTOCOL.md), and
[public evidence bundle](artifacts/emoji_family_exploratory_v1/analysis/report.md).

### Multifamily tokenizer census status

The frozen tokenizer-only census completed all 14 locally available roster
entries across mac1, mac2, and furnace: 115 fixed strings, four contexts, 6,440
tokenization rows, 19,665 pairwise rows, zero model forwards, and zero protected
target access. The 14 artifacts formed seven exact output classes on the fixed
surface; five classes reproduced exactly across nodes.

Only six strings had the same raw token count across all seven classes. The
largest range was 13 tokens for the family ZWJ sequence. For both blue circle
and blue square, no single fixed-panel candidate matched both token count and a
one-token prefix across all seven classes in any of the raw, leading-space, or
glyph-prompt contexts. Existing ASCII controls did not provide a universal
equal-count match either.

This result calls for separately frozen, tokenizer-specific control panels; it
does not remove tokenization as a confound, update Milestone 2, select a layer,
or establish tokenizer-independent structure. See the [complete descriptive
result](docs/MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.md), [frozen
protocol](docs/MULTIFAMILY_TOKENIZER_CENSUS_V0.md), and [compact verified
aggregate](artifacts/multifamily_tokenizer_census_v0/aggregate.json).

### Multifamily colored-shape geometry v0 status

The two role-bound runs and joint exact analysis are complete after the public
freeze. At the prespecified midpoint, Gemma 2 2B 4-bit produced parallelism
`0.114857969` (raw p = `0.058333333`, Holm p = `0.116666667`) and OLMo 3 7B
BF16 produced `0.024628040` (raw and Holm p = `0.275`). Neither rejected, so the
predeclared outcome is `no_dual_model_recurrence`.

All ten fixed-depth rows remain public; the non-midpoint Gemma rows are not
promoted despite smaller descriptive exact p-values. Both runs used zero
generation, intervention, and protected-target calls. The compact evidence
contains both activation arrays, and all source, relay, destination, and joint
analysis checks passed. This closes the observational side track, not a causal,
confirmatory, backend-parity, quantization, scale, or model-general claim. See
the [complete result](docs/MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.md),
[frozen protocol](docs/MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0.md), and [public
evidence](artifacts/multifamily_colored_shape_geometry_v0/README.md).

### Multifamily matched-slot geometry v0 status

The frozen 5-family × 10-slot observational study completed on the same Gemma
and OLMo roles. Gemma's all-depth slot fraction was `0.204304805` against a
randomization-null mean of `0.199984463` (Holm p = `0.2085`). OLMo's was
`0.500391869` against `0.200184835` (Holm p = `0.0001`). The predeclared pattern
is `olmo_only_token_structured_recurrence`.

This is the tokenizer-conditioned branch the design was built to distinguish:
Gemma uses 50 distinct atomic tokens, while OLMo uses the exact form
`[shared_prefix, family_token, shared_slot_token]`. OLMo's result therefore has
a sufficient shared-token explanation and does not establish semantic or
tokenizer-independent recurrence. The complete result, the failed first
serialization attempt, and the prospective serialization-only repair are all
retained in the [result document](docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.md)
and [public evidence](artifacts/multifamily_matched_slot_geometry_v0/README.md).

### Multifamily common-suffix carryover v0 status

The prospective follow-up moved the readout one token past each raw glyph to a
common period or newline token. Gemma's two-context all-depth statistic was
`0.203443011` against a null mean of `0.200044692` (Holm p = `0.30295`). OLMo's
was `0.537464703` against `0.199977865` (Holm p = `0.0001`). The predeclared
pattern is `olmo_only_common_suffix_carryover`.

OLMo was closely matched across the two secondary context summaries (period
`0.538985382`; newline `0.535944025`). The shared-slot geometry is therefore not
confined to reading the slot token itself, but remains visible one common token
later. Short-range propagation from the immediately preceding token structure
is still a sufficient explanation; this is not semantic, causal, confirmatory,
or tokenizer-independent evidence. See the [complete result](docs/MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.md),
[frozen protocol](docs/MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0.md), and [public
evidence](artifacts/multifamily_common_suffix_carryover_v0/README.md).

### Multifamily carrier-distance v0 status

The prospective observational falsification is complete. It kept each full
input and current carrier-token identity fixed while reading `resid_post` at
distances 1, 2, 4, and 8 inside repeated `" a"` and repeated `" |"` carriers.
The sole primary decision required both distance-1 recurrence and a positive
fixed log-distance attenuation contrast in each model-level
intersection-union test.

Gemma's distance-1 component was null-centered. Llama and OLMo each had a raw
distance-1 component p-value at the `0.00005` permutation floor, but their attenuation p-values
were `0.188` and `0.9977`, respectively. The IUT/Holm p-values were therefore
`1.0`, `0.564`, and `1.0` for Gemma, Llama, and OLMo, yielding
`no_model_distance_attenuation`. The descriptive distance-8 profiles remain
elevated for Llama (`0.369105`) and OLMo (`0.527099`), but tail rows carry no
separate multiplicity decision. The result does not establish monotonic
persistence, a duration threshold, semantics, mechanism, causality, tokenizer
independence, or a direct cross-model magnitude contrast. Llama's earlier
Stage-A parity failure also remains in force. See the [complete
result](docs/MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.md), [frozen
protocol](docs/MULTIFAMILY_CARRIER_DISTANCE_V0.md), and [public
evidence](artifacts/multifamily_carrier_distance_v0/README.md).

### Dense CUDA carrier-distance T6 status

The post-T5 four-cell BF16 Transformers/CUDA replication is complete with
`no_dense_model_distance_attenuation`. Gemma 2 2B IT, Gemma 3 4B IT, and Gemma
3 12B IT did not reject the distance-1 component. Mistral 7B Instruct v0.3 did
so at the `0.00005` permutation floor, but its fixed attenuation p-value was
`0.46975`. No model-level IUT survived the four-model Holm family.

All four 400-forward runs and the 160-row analysis validated, with zero
intervention, generation, and protected-target calls. The start gate was met by
a free-furnace recheck and a natural receiver-owned `resource:furnace` Codex
`Stop` surface. The result neither pools with T5 nor supports scale, tokenizer,
backend, semantic, causal, or confirmatory claims. See the [complete
result](docs/MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.md), [frozen
protocol](docs/MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0.md), and [public
evidence](artifacts/multifamily_dense_cuda_carrier_distance_v0/README.md).

### Mistral 7B base depth-by-distance T7 status

The post-T6 endpoint was frozen before the previously unobserved Mistral 7B
v0.3 base-model run. Distance-1 recurrence was `0.377524026` and the fixed
early-minus-late attenuation interaction was `0.149104068`; both one-sided raw
p-values reached the `0.00005` permutation floor, so the single IUT rejected.
Depth-0 attenuation was `+0.114009450`, while the later-depth mean was
`-0.035094618`.

The 20 base depth-by-distance cells were descriptively close to the already
known T6 Instruct profile (`r = 0.996785730`), but the model and endpoint were
selected after T6 and the checkpoints are related. No equivalence,
instruction-tuning, independent-confirmation, semantic, causal, or Phase I
gate claim is made. See the [complete result](docs/MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.md),
[frozen protocol](docs/MISTRAL7B_BASE_DEPTH_DISTANCE_V0.md), and [public
evidence](artifacts/mistral7b_base_depth_distance_v0/README.md).

### Mistral 7B semantic atlas T8 status

T8 began as a high-n observational atlas. The first batch-64 acquisition failed
its fixed batch-one equivalence check 0/18, so the thresholds were retained and
the exact 892-item grid was recaptured canonically at batch size one. All 28
shards and 192,672 FP32 vectors validated; an independent 18-case repeat was
bit-exact.

On 842 unseen discovery items, equal-cell layer-31 glyph→official-name top-1
retrieval was `0.136580` against chance `0.001188`; glyph→`U+...` retrieval was
`0.001188`. The contrast persisted in 760 five-token glyphs with one shared
three-token prefix and in the 43-item equal glyph/name token-count stratum.
Those discovery analyses were descriptive and partly post-outcome. A later
protocol froze one layer-31 endpoint before any reserve forward, then acquired
all 292 reserved items exactly once. The minimum of the eight glyph/name minus
glyph/codepoint top-1 contrasts was `0.171233` against a practical floor of
`0.02`; the common-permutation p-value was `0.00005`. T8's narrow alignment
question is therefore prospectively confirmed and closed in this model. It is
not a semantic-causal or model-general result. See the [confirmation result](docs/MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0_RESULTS.md),
[frozen protocol](docs/MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0.md), and
[public evidence](artifacts/mistral7b_semantic_atlas_reserve_confirmation_v0/README.md).

### Semantic atlas T10 status

T10 is complete with the registered negative outcome
`cross_model_replication_not_established_under_frozen_rule`. All nine exact
model/tokenizer cells completed the same 292 items, three views, two carriers,
four distances, and batch-one transport: 333 shards, 15,768 model forwards,
and 126,144 FP32 readout vectors in total.

Every model-cell IUT was statistically significant after comparing the all-item
component with an exact three-view token-count-stratified component. The four
core p-values were each `0.00005`, yielding a Bonferroni partial-conjunction
`p = 0.0001`. The frozen primary nevertheless failed because only Llama 3.2 3B
base and Qwen 2.5 7B base cleared the `0.02` practical floor in both components;
the rule required at least three of four core cells. Across all nine cells,
Llama 3.2 3B base, Qwen 2.5 7B base, and Mistral 7B Instruct v0.3 passed the
bounded Holm-plus-practical cell rule.

An implementation audit also corrected the T8/T9 endpoint terminology:
`output.hidden_states[-1]` is the returned final normalized hidden state, not
the raw final decoder-block output. T10 preserves that API endpoint as primary
and captures the raw block output as a non-rescuing secondary. Exact token-count
matching retained 281--287 items and did not erase the contrast, but this does
not establish tokenizer independence. The monotone four-point Qwen profile and
the related Mistral-Instruct cell remain descriptive and do not authorize scale
or tuning claims. See the [complete result](docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.md),
[frozen protocol](docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.md), and
[compact evidence](artifacts/semantic_atlas_cross_model_replication_v0/README.md).

### T10 diagnostics, T11 discovery, T12 confirmation, and T13-EA analysis

T10-D keeps the negative T10 primary unchanged and reconstructs the raw
activation-derived metrics exactly: 333 shards, 36 arrays, and 84,096 scalar
values were checked with zero mismatches. It found positive continuous
glyph/name margins in all 72 model-context cells, but sharply uneven item
coverage, model-specific carrier-distance profiles, weak codepoint geometry,
and model-conditioned raw-to-final changes. No item was a top-1 hit in all nine
models. These are diagnostics for the next design, not a rescue of T10.

T11 then completed the frozen nine-model discovery atlas: 477 shards, 73,566
model forwards, 982,512 FP32 readout vectors, and zero reserve forwards at T11
completion. Exact
target-token-length controls passed in every required system. Returned-final
glyph/name margins were positive in all 72 cells for presentation, modifier,
ZWJ, and regional systems; keycaps were positive in 65/72. The most coherent
narrow follow-up is the ZWJ `presentation_or_fusion` contrast, positive in
65/72 cells, while regional flags showed a mixed whole-name and component
pattern. Cross-model item agreement remained weak, only 8/36 ordered Qwen
profiles were strictly increasing, and first-token-matched coverage was sparse
for atomic and presentation systems. T11 is therefore an exploratory atlas,
not a semantic, causal, tokenizer-independent, scale, tuning, or model-general
result. See the [T11 result](docs/GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.md),
[compact evidence](artifacts/glyph_system_decomposition_v0/README.md), and
[frozen protocol](docs/GLYPH_SYSTEM_DECOMPOSITION_V0.md).

T12 subsequently froze and opened the complete 96-item ZWJ and 64-item
regional-flag reserve subsets across the same nine roles and eight contexts.
All 9,792 forwards and 39,168 returned-final vectors completed. Neither
registered hypothesis was confirmed. ZWJ had statistic `0.000369`, raw
`p = 0.05496`, and Holm `p = 0.10992`. Regional presentation/fusion was weakly
directional (`0.002767`, component `p = 0.03538`), but regional component
tracking was `0.000666`, `p = 0.12950`; the dual IUT/Holm decision was therefore
`p = 0.12950`. All three components missed their practical floors and had zero
models at those floors. An analyzer-independent validator reconstructed 432
cell medians, all three 49,999-draw tests, and every gate with zero mismatches.
See the [T12 result](docs/GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.md),
[compact evidence](artifacts/glyph_system_reserve_confirmation_v0/README.md),
and [T13 decision map](docs/EMOJI_STEERING_SPECIFICITY_ATLAS_V0.md).

T13-EH completed the resource-ordered harvest over the exposed 192-item T11
depth population and all 32 public prestage targets. All nine frozen roles
contributed the source bank, and three prespecified base roles contributed the
complete 383,232-row response surface. T13-EA then completed the registered
F1–F6 exploratory point analysis. The historical v0 exact-JS zero gate remains
a preserved fail-closed result; the separately frozen v1 amendment passed only
the exact primitive no-op checks plus its bounded float32 JS round-trip check.

The point estimates sharpen the next question to whether structured source
directions explain intervention response beyond generic target susceptibility
and null-direction dependence. They do not establish unique emoji specificity,
meaning, mechanism, behavior, scale, or model generality. The registered
cluster bootstrap remains at 0/20,000, and T13-EA has no primary
hypothesis, significance decision, or confirmatory verdict. See the [T13-EA
result](docs/EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.md), [bootstrap
execution freeze](docs/EMOJI_STEERING_SPECIFICITY_BOOTSTRAP_EXECUTION_V1.md), [zero-gate
amendment](docs/EMOJI_STEERING_SPECIFICITY_ZERO_GATE_AMENDMENT_V1.md), [compact
evidence](artifacts/emoji_steering_specificity_analysis_v0/README.md), and
[T13-EH protocol](docs/EMOJI_STEERING_SPECIFICITY_HARVEST_V0.md).

### T14-X expansion and T14-C causal closeout

T14-X completed 559,488 response rows across Llama 3.2 3B, OLMo 2 1B,
and four Qwen 2.5 sizes at depths 0.875 and 1.0. All 12 headline
structured-minus-covariance-null JS intervals excluded zero, but the signed
classification was nine positive and three negative. Qwen was non-monotonic:
0.5B was positive, 1.5B changed sign at the final depth, 3B was negative at
both depths, and 7B was positive again. Source-form, null-family, and sign
decompositions were heterogeneous, so this is an exploratory response-anisotropy
regime rather than universal glyph privilege or a scale law.

T14-C was frozen before that outcome was opened. Its fixed selector chose
Llama 3.2 3B `mlp_out` block 24 from eight candidate sites using 32 public
targets. A new 192-target C1 v2 bank was then materialized and used once. All
zero, restoration, positive-control, and upstream-sham engineering gates
passed. The registered treatment estimate was `0.00172230`, below its `0.002`
floor; necessity was `-0.00057689`; sufficiency was `0.00002126`, below its
`0.0005` floor. The intersection-union test therefore did not reject. This
closes the targeted-causal paper gate with a negative result, while leaving
`confirmatory_claim_authorized: false`. See the [complete bilingual
result](docs/EMOJI_STEERING_T14_X_T14_C_RESULTS_V0.md).

### T15-A emoji × word incongruence interaction

T15-A completed 393,472 steering-response rows across OLMo 2 1B, Llama 3.2
3B, Qwen 2.5 3B, and Qwen 2.5 7B base models. At the frozen primary dose,
balanced within-axis interaction directions produced more coherent
full-vocabulary response fingerprints than three structurally matched
cross-axis interactions in all 16 model × depth × sign cells. Every
20,000-replicate target-bootstrap interval was entirely above zero.

The secondary families prevent a simple strength story. Individual
incongruent-pair additivity residuals had no common positive excess; JS, total
variation, logit RMS, entropy, argmax flips, word-versus-emoji main effects,
source order, depth, and dose were heterogeneous. The result is therefore an
exploratory non-additive response-*shape* candidate, not evidence of emoji
meaning, contradiction detection, behavior, or a causal circuit. The original
analyzer failed closed on an 8-versus-16 repeat assertion; a versioned
post-open repair changed only that assertion and left every estimand and
bootstrap unchanged. See the [bilingual result](docs/EMOJI_WORD_INCONGRUENCE_INTERACTION_V0_RESULTS.md),
[frozen protocol](docs/EMOJI_WORD_INCONGRUENCE_INTERACTION_V0.md), and
[compact closeout](validation/emoji_word_incongruence_interaction_v0/t15a_closeout.json).

### T15-B prospective holdout replication

T15-B replaced all eight axes, all 48 targets, and both model roles, then
compared each true interaction with all seven non-self cross-axis controls.
The frozen R1 gate pooled the two depths and two signs within each target but
kept the two models separate. SmolLM2 1.7B base had a target median of
`+0.020422` with interval `[0.012887, 0.031510]`; Mistral 7B Instruct v0.3 had
`+0.060397` with `[0.056621, 0.062194]`. Both lower bounds passed the frozen
one-sided Bonferroni threshold, so the two-model intersection decision is
`support`.

The result is narrower than a universal cell effect: six of eight separate
primary-dose model × depth × sign intervals were positive and two were mixed.
A0 and A3 source diagnostics were mixed in all four model × depth cells, and
energy, main-effect, order, depth, and dose families remained heterogeneous.
T15-B therefore supplies an independent-model replication of the operational
response-shape candidate, not evidence of meaning, contradiction detection,
behavior, or a causal circuit. See the [bilingual result](docs/EMOJI_WORD_INCONGRUENCE_REPLICATION_V0_RESULTS.md),
[frozen protocol](docs/EMOJI_WORD_INCONGRUENCE_REPLICATION_V0.md), and
[compact closeout](validation/emoji_word_incongruence_replication_v0/t15b_closeout.json).

### E2 engineering results

The frozen Llama 3.2 3B BF16 Stage-A v2 engineering validation completed with
`status: validation_failed` and `scientific_result: false`. It passed 33/60 parity checks: tokenization and
within-backend determinism passed 10/10, exact zero-hook behavior passed 10/10,
baseline checks passed 6/10, changed-output checks passed 7/10, composite-delta
checks passed 0/10, and intervention-fidelity checks passed 0/10. All ten
activation-delta subcomparisons passed, but all composite delta checks failed
because the corresponding logit deltas did not meet the frozen thresholds.

The machine-local speed gate also failed. Aggregate median latency was
132.127833 ms for Transformers/MPS and 230.138000 ms for MLX: MLX used
1.741782892 times the latency, equivalent to the receipt's recorded
`0.574124367x` speedup. The sole specified backend change affecting numerical
semantics in v2—the BF16-to-FP32 cast immediately before NumPy export—allowed
the full validation to complete, but did not qualify MLX for this cell.

This is a negative engineering qualification only. The run accessed no study
target bank or confirmatory or causal outcome, produced no emoji-family,
semantic, causal, or cross-model result, and closes no paper gate. The v1 export
failure remains preserved. See the [complete E2 result](docs/LLAMA32_3B_MLX_VALIDATION_RESULTS.md),
[frozen protocol](docs/LLAMA32_3B_MLX_VALIDATION_PROTOCOL.md), and
[machine-readable receipt](validation/mlx_llama32_3b_bf16_parity_v2/receipt.json).
Stage A3 then screened the same pinned BF16-weight artifact with separate FP16
and FP32 runtime-compute candidates. Both candidates passed exact artifact and
parameter identity, prompt/token identity, determinism, the unchanged
zero-vector threshold, and backend-specific fidelity. Both failed only the
frozen machine-local speed requirement. FP16 recorded 165.0765625 ms for
Transformers/MPS and 322.9998125 ms for MLX; FP32 recorded 465.013771 ms and
458.619459 ms. The latter is approximately a 1.375% reduction, not the required
5%. The deterministic result was therefore
`selection.selected_runtime_dtype: null` and
`selection.decision: no_go_no_eligible_numeric_candidate`.

Stage A3 did not run full cross-backend parity, so FP32 is not qualified despite
its strong within-backend fidelity. No formal v3 validator or MLX science grid
was run or authorized, and the v2 failure remains unchanged. See the
[Stage-A3 result](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.md),
[frozen numeric-screen protocol](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.md), and
[atomic receipt](validation/mlx_llama32_3b_numeric_screen_v1/receipt.json).
The research owner selected a separate Transformers/MPS scientific route. Its
v1 static freeze stopped at tokenizer preflight before model-weight loading or
any forward because the audit conflated raw and contextual wrapper tokenization.
V1 is retired with [no scientific
outcome](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.md). The same
50-emoji primary arm and independently centered 35-emoji token-structural
sensitivity arm are being rebound under the corrected, separately versioned
[v2 protocol](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.md). This MPS-only study
does not reinterpret the MLX no-go or relax either MLX threshold.

## Install

GlyphProbe requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Choose the execution path you need:

```bash
# Apple silicon
pip install -e '.[mlx,torch,dev]'

# Raw Hugging Face Transformers
pip install -e '.[torch,dev]'

# TransformerLens
pip install -e '.[lens,dev]'

# TransformerLens + SAELens
pip install -e '.[sae,dev]'

# OpenAI-compatible serving controls
pip install -e '.[server,dev]'
```

Initialize a self-contained experiment workspace:

```bash
glyphprobe init ./glyphprobe-experiment
cd glyphprobe-experiment
```

The copied workspace contains versioned configs, the panel, source wrappers, target cases, and backend-matrix examples.

## Closed-loop smoke test

The deterministic mock backend verifies joins and artifact generation without downloading a model:

```bash
glyphprobe plan -c configs/v1_smoke.yaml --num-layers 8
glyphprobe run  -c configs/v1_smoke.yaml
```

Mock output is plumbing evidence only. It must not be cited as model evidence.

## Reproduce the pinned MLX cell

The standard config is offline-first and already binds the scientific run to the checked-in parity-receipt hash:

```bash
glyphprobe inspect -c configs/v1_mlx_standard.yaml
glyphprobe plan -c configs/v1_mlx_standard.yaml --load-model
glyphprobe run -c configs/v1_mlx_standard.yaml
```

To requalify after changing backend code or the model cell, return from the starter workspace to the repository checkout root and write a candidate receipt without overwriting the pinned one:

```bash
cd ..  # repository checkout root
python scripts/validate_mlx_gpt2_parity.py \
  --output validation/mlx_gpt2_parity/receipt.candidate.json
shasum -a 256 validation/mlx_gpt2_parity/receipt.candidate.json
```

Promote a passing candidate and update `validation_receipt_sha256` in both standard configs as one reviewed change. A newly generated receipt contains fresh timing samples, so its SHA-256 is expected to differ even when all gates pass.

The validation scope is intentionally narrow:

- model: `openai-community/gpt2` at the pinned revision above;
- dtype: FP32;
- site: full-sequence `resid_post`;
- standard layers: 2, 4, 7, and 9;
- prompt-length buckets: 3, 9, 10, and 22 tokens in the recorded receipt;
- intervention: a sealed fixed FP32 vector, plus exact zero-hook checks.

Changing the model, revision, dtype, quantization, component site, or implementation creates a new experimental cell and requires a new parity receipt. MLX support does not make MLX and PyTorch outputs generally interchangeable.

## Other execution paths

TransformerLens remains the canonical named-hook path:

```bash
glyphprobe run -c configs/v1_standard.yaml \
  --backend lens \
  --model openai-community/gpt2 \
  --device cuda \
  --dtype float32
```

Raw Transformers uses conservative model-family module discovery:

```bash
glyphprobe run -c configs/v1_standard.yaml \
  --backend transformers \
  --model openai-community/gpt2 \
  --device cuda \
  --dtype float32
```

OpenAI-compatible adapters (`vllm`, `llamacpp`, `ollama`, `lmstudio`, and `openai`) provide surface controls. Standard serving APIs do not expose residual streams, so these runs are stamped `surface-observational-only` and cannot substitute for activation intervention.

## What the standard matrix controls

- panel-centroid removal and a neutral-glyph source baseline;
- separately estimated wrapper-subset direction seeds;
- norm-matched random directions projected outside the panel-direction span;
- exact zero-vector hook controls;
- three positive RMS strengths, global RMS clipping, and sign flips;
- repeated group-stratified target splits;
- within-target glyph-label permutations;
- cross-seed output-fingerprint comparisons;
- token IDs, Unicode code points, UTF-8 bytes, and wrapper token counts.

Full-vocabulary logit deltas are compressed into deterministic, unit-normalized CountSketch fingerprints. These are comparison objects, not semantic labels.

## Read the artifacts conservatively

The current standard result is heterogeneous. The median fingerprint advantage is positive, and every layer median is positive, but 11 of 36 layer–seed–strength cells are non-positive. The primary glyphs are length-balanced at three tokens each, yet token identities differ; the neutral `·` control is one token, and the blue-circle token sequence has a distinct middle token. The permutation screen reaches the finite floor `1/1001` in all 36 cells, but those values are not multiplicity-corrected global significance tests.

Target prompts are the principal sampling clusters. Direction seeds remain nested repeated estimates and must not be counted as independent observations. Iso-KL, SAE, generation, other hook sites, path patching, and cross-model replication were not run in this cell.

The compact public evidence package omits the approximately 74 MiB (77.3 MB) raw `interventions.jsonl` ledger and model-dependent NPZ arrays. Published summaries and manifests identify what was retained or omitted; a paper-grade release must preserve or archive the complete sealed run separately.

## Documentation

Project-authored public documentation is maintained in English and Japanese:

| Topic | English | Japanese |
|---|---|---|
| Scientific contract | [SCIENTIFIC_CONTRACT.md](docs/SCIENTIFIC_CONTRACT.md) | [SCIENTIFIC_CONTRACT.ja.md](docs/SCIENTIFIC_CONTRACT.ja.md) |
| Backend boundaries | [BACKENDS.md](docs/BACKENDS.md) | [BACKENDS.ja.md](docs/BACKENDS.ja.md) |
| Metrics | [METRICS.md](docs/METRICS.md) | [METRICS.ja.md](docs/METRICS.ja.md) |
| Current results | [RESULTS_V1.md](docs/RESULTS_V1.md) | [RESULTS_V1.ja.md](docs/RESULTS_V1.ja.md) |
| Milestone 2 results | [MILESTONE2_RESULTS.md](docs/MILESTONE2_RESULTS.md) | [MILESTONE2_RESULTS.ja.md](docs/MILESTONE2_RESULTS.ja.md) |
| Milestone 2 protocol | [MILESTONE2_PROTOCOL.md](docs/MILESTONE2_PROTOCOL.md) | [MILESTONE2_PROTOCOL.ja.md](docs/MILESTONE2_PROTOCOL.ja.md) |
| E1 exploratory results | [EMOJI_FAMILY_EXPLORATORY_RESULTS.md](docs/EMOJI_FAMILY_EXPLORATORY_RESULTS.md) | [EMOJI_FAMILY_EXPLORATORY_RESULTS.ja.md](docs/EMOJI_FAMILY_EXPLORATORY_RESULTS.ja.md) |
| E1 exploratory protocol | [EMOJI_FAMILY_EXPLORATORY_PROTOCOL.md](docs/EMOJI_FAMILY_EXPLORATORY_PROTOCOL.md) | [EMOJI_FAMILY_EXPLORATORY_PROTOCOL.ja.md](docs/EMOJI_FAMILY_EXPLORATORY_PROTOCOL.ja.md) |
| Multifamily tokenizer census results | [MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.md](docs/MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.md) | [MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.ja.md](docs/MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.ja.md) |
| Multifamily tokenizer census protocol | [MULTIFAMILY_TOKENIZER_CENSUS_V0.md](docs/MULTIFAMILY_TOKENIZER_CENSUS_V0.md) | [MULTIFAMILY_TOKENIZER_CENSUS_V0.ja.md](docs/MULTIFAMILY_TOKENIZER_CENSUS_V0.ja.md) |
| Multifamily colored-shape geometry v0 results | [MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.md](docs/MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.md) | [MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.ja.md](docs/MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.ja.md) |
| Multifamily colored-shape geometry v0 | [MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0.md](docs/MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0.md) | [MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0.ja.md](docs/MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0.ja.md) |
| Multifamily matched-slot geometry v0 results | [MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.md](docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.md) | [MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.ja.md](docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.ja.md) |
| Multifamily matched-slot geometry v0 | [MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0.md](docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0.md) | [MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0.ja.md](docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0.ja.md) |
| Matched-slot analysis repair v1 | [MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_ANALYSIS_REPAIR_V1.md](docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_ANALYSIS_REPAIR_V1.md) | [MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_ANALYSIS_REPAIR_V1.ja.md](docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_ANALYSIS_REPAIR_V1.ja.md) |
| Multifamily common-suffix carryover v0 results | [MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.md](docs/MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.md) | [MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.ja.md](docs/MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.ja.md) |
| Multifamily common-suffix carryover v0 | [MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0.md](docs/MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0.md) | [MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0.ja.md](docs/MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0.ja.md) |
| Multifamily carrier-distance v0 results | [MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.md](docs/MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.md) | [MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.ja.md](docs/MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.ja.md) |
| Multifamily carrier-distance v0 | [MULTIFAMILY_CARRIER_DISTANCE_V0.md](docs/MULTIFAMILY_CARRIER_DISTANCE_V0.md) | [MULTIFAMILY_CARRIER_DISTANCE_V0.ja.md](docs/MULTIFAMILY_CARRIER_DISTANCE_V0.ja.md) |
| Multifamily dense CUDA carrier-distance v0 results | [MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.md](docs/MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.md) | [MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.ja.md](docs/MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.ja.md) |
| Multifamily dense CUDA carrier-distance v0 | [MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0.md](docs/MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0.md) | [MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0.ja.md](docs/MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0.ja.md) |
| Mistral 7B base depth-by-distance v0 results | [MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.md](docs/MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.md) | [MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.ja.md](docs/MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.ja.md) |
| Mistral 7B base depth-by-distance v0 | [MISTRAL7B_BASE_DEPTH_DISTANCE_V0.md](docs/MISTRAL7B_BASE_DEPTH_DISTANCE_V0.md) | [MISTRAL7B_BASE_DEPTH_DISTANCE_V0.ja.md](docs/MISTRAL7B_BASE_DEPTH_DISTANCE_V0.ja.md) |
| Mistral 7B semantic atlas v0 | [MISTRAL7B_SEMANTIC_ATLAS_V0.md](docs/MISTRAL7B_SEMANTIC_ATLAS_V0.md) | [MISTRAL7B_SEMANTIC_ATLAS_V0.ja.md](docs/MISTRAL7B_SEMANTIC_ATLAS_V0.ja.md) |
| Mistral 7B semantic atlas batch-one v1 results | [MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1_RESULTS.md](docs/MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1_RESULTS.md) | [MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1_RESULTS.ja.md](docs/MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1_RESULTS.ja.md) |
| Mistral 7B semantic atlas batch-one v1 | [MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1.md](docs/MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1.md) | [MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1.ja.md](docs/MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1.ja.md) |
| Mistral 7B semantic atlas analysis plan | [MISTRAL7B_SEMANTIC_ATLAS_V0_ANALYSIS.md](docs/MISTRAL7B_SEMANTIC_ATLAS_V0_ANALYSIS.md) | [MISTRAL7B_SEMANTIC_ATLAS_V0_ANALYSIS.ja.md](docs/MISTRAL7B_SEMANTIC_ATLAS_V0_ANALYSIS.ja.md) |
| Mistral 7B semantic atlas token sensitivity | [MISTRAL7B_SEMANTIC_ATLAS_TOKEN_STRUCTURE_V0.md](docs/MISTRAL7B_SEMANTIC_ATLAS_TOKEN_STRUCTURE_V0.md) | [MISTRAL7B_SEMANTIC_ATLAS_TOKEN_STRUCTURE_V0.ja.md](docs/MISTRAL7B_SEMANTIC_ATLAS_TOKEN_STRUCTURE_V0.ja.md) |
| Mistral 7B semantic atlas reserve confirmation v0 results | [MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0_RESULTS.md](docs/MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0_RESULTS.md) | [MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0_RESULTS.ja.md](docs/MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0_RESULTS.ja.md) |
| Mistral 7B semantic atlas reserve confirmation v0 | [MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0.md](docs/MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0.md) | [MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0.ja.md](docs/MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0.ja.md) |
| Semantic atlas cross-model replication v0 | [SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.md](docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.md) | [SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.ja.md](docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.ja.md) |
| Semantic atlas cross-model replication v0 results | [SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.md](docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.md) | [SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.ja.md](docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.ja.md) |
| Semantic atlas cross-model diagnostics v1 | [SEMANTIC_ATLAS_CROSS_MODEL_DIAGNOSTICS_V1.md](docs/SEMANTIC_ATLAS_CROSS_MODEL_DIAGNOSTICS_V1.md) | [SEMANTIC_ATLAS_CROSS_MODEL_DIAGNOSTICS_V1.ja.md](docs/SEMANTIC_ATLAS_CROSS_MODEL_DIAGNOSTICS_V1.ja.md) |
| Glyph-system decomposition atlas v0 results (T11) | [GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.md](docs/GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.md) | [GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.ja.md](docs/GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.ja.md) |
| Glyph-system decomposition atlas v0 (T11) | [GLYPH_SYSTEM_DECOMPOSITION_V0.md](docs/GLYPH_SYSTEM_DECOMPOSITION_V0.md) | [GLYPH_SYSTEM_DECOMPOSITION_V0.ja.md](docs/GLYPH_SYSTEM_DECOMPOSITION_V0.ja.md) |
| Glyph-system reserve confirmation v0 results (T12) | [GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.md](docs/GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.md) | [GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.ja.md](docs/GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.ja.md) |
| Glyph-system reserve confirmation v0 (T12) | [GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0.md](docs/GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0.md) | [GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0.ja.md](docs/GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0.ja.md) |
| Glyph-name depth trajectory results (T17) | [GLYPH_NAME_DEPTH_TRAJECTORY_V0_RESULTS.md](docs/GLYPH_NAME_DEPTH_TRAJECTORY_V0_RESULTS.md) | [GLYPH_NAME_DEPTH_TRAJECTORY_V0_RESULTS.ja.md](docs/GLYPH_NAME_DEPTH_TRAJECTORY_V0_RESULTS.ja.md) |
| Fresh composite-glyph confirmation protocol (T18) | [FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0.md](docs/FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0.md) | [FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0.ja.md](docs/FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0.ja.md) |
| Fresh composite-glyph confirmation results (T18) | [FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0_RESULTS.md](docs/FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0_RESULTS.md) | [FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0_RESULTS.ja.md](docs/FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0_RESULTS.ja.md) |
| T18 fresh lexical paper story | [PAPER_STORY_T18_FRESH_LEXICAL_V0.md](docs/PAPER_STORY_T18_FRESH_LEXICAL_V0.md) | [PAPER_STORY_T18_FRESH_LEXICAL_V0.ja.md](docs/PAPER_STORY_T18_FRESH_LEXICAL_V0.ja.md) |
| T19 lexical alias and symbol-control protocol | [T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.md](docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.md) | [T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.ja.md](docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.ja.md) |
| T19 lexical and component-causal results | [T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0_RESULTS.md](docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0_RESULTS.md) | [T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0_RESULTS.ja.md](docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0_RESULTS.ja.md) |
| T19 lexical-neighborhood paper story | [PAPER_STORY_T19_LEXICAL_NEIGHBORHOOD_V0.md](docs/PAPER_STORY_T19_LEXICAL_NEIGHBORHOOD_V0.md) | [PAPER_STORY_T19_LEXICAL_NEIGHBORHOOD_V0.ja.md](docs/PAPER_STORY_T19_LEXICAL_NEIGHBORHOOD_V0.ja.md) |
| Phase I first-draft paper package | [README.md](paper/README.md) | [README.ja.md](paper/README.ja.md) |
| Emoji steering specificity atlas v0 (T13 decision map) | [EMOJI_STEERING_SPECIFICITY_ATLAS_V0.md](docs/EMOJI_STEERING_SPECIFICITY_ATLAS_V0.md) | [EMOJI_STEERING_SPECIFICITY_ATLAS_V0.ja.md](docs/EMOJI_STEERING_SPECIFICITY_ATLAS_V0.ja.md) |
| Emoji steering specificity harvest v0 (T13-EH) | [EMOJI_STEERING_SPECIFICITY_HARVEST_V0.md](docs/EMOJI_STEERING_SPECIFICITY_HARVEST_V0.md) | [EMOJI_STEERING_SPECIFICITY_HARVEST_V0.ja.md](docs/EMOJI_STEERING_SPECIFICITY_HARVEST_V0.ja.md) |
| Emoji steering specificity analysis v0 (T13-EA) | [EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0.md](docs/EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0.md) | [EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0.ja.md](docs/EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0.ja.md) |
| Emoji steering specificity analysis v0 results | [EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.md](docs/EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.md) | [EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.ja.md](docs/EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.ja.md) |
| Emoji steering specificity bootstrap execution v1 | [EMOJI_STEERING_SPECIFICITY_BOOTSTRAP_EXECUTION_V1.md](docs/EMOJI_STEERING_SPECIFICITY_BOOTSTRAP_EXECUTION_V1.md) | [EMOJI_STEERING_SPECIFICITY_BOOTSTRAP_EXECUTION_V1.ja.md](docs/EMOJI_STEERING_SPECIFICITY_BOOTSTRAP_EXECUTION_V1.ja.md) |
| Emoji steering specificity zero-gate amendment v1 | [EMOJI_STEERING_SPECIFICITY_ZERO_GATE_AMENDMENT_V1.md](docs/EMOJI_STEERING_SPECIFICITY_ZERO_GATE_AMENDMENT_V1.md) | [EMOJI_STEERING_SPECIFICITY_ZERO_GATE_AMENDMENT_V1.ja.md](docs/EMOJI_STEERING_SPECIFICITY_ZERO_GATE_AMENDMENT_V1.ja.md) |
| Emoji steering specificity compact evidence | [README.md](artifacts/emoji_steering_specificity_analysis_v0/README.md) | [README.ja.md](artifacts/emoji_steering_specificity_analysis_v0/README.ja.md) |
| T14-X expansion and T14-C causal results | [EMOJI_STEERING_T14_X_T14_C_RESULTS_V0.md](docs/EMOJI_STEERING_T14_X_T14_C_RESULTS_V0.md) | [EMOJI_STEERING_T14_X_T14_C_RESULTS_V0.ja.md](docs/EMOJI_STEERING_T14_X_T14_C_RESULTS_V0.ja.md) |
| Emoji × word incongruence interaction v0 protocol (T15-A) | [EMOJI_WORD_INCONGRUENCE_INTERACTION_V0.md](docs/EMOJI_WORD_INCONGRUENCE_INTERACTION_V0.md) | [EMOJI_WORD_INCONGRUENCE_INTERACTION_V0.ja.md](docs/EMOJI_WORD_INCONGRUENCE_INTERACTION_V0.ja.md) |
| Emoji × word incongruence interaction v0 results (T15-A) | [EMOJI_WORD_INCONGRUENCE_INTERACTION_V0_RESULTS.md](docs/EMOJI_WORD_INCONGRUENCE_INTERACTION_V0_RESULTS.md) | [EMOJI_WORD_INCONGRUENCE_INTERACTION_V0_RESULTS.ja.md](docs/EMOJI_WORD_INCONGRUENCE_INTERACTION_V0_RESULTS.ja.md) |
| Prospective emoji × word replication v0 protocol (T15-B) | [EMOJI_WORD_INCONGRUENCE_REPLICATION_V0.md](docs/EMOJI_WORD_INCONGRUENCE_REPLICATION_V0.md) | [EMOJI_WORD_INCONGRUENCE_REPLICATION_V0.ja.md](docs/EMOJI_WORD_INCONGRUENCE_REPLICATION_V0.ja.md) |
| Prospective emoji × word replication v0 results (T15-B) | [EMOJI_WORD_INCONGRUENCE_REPLICATION_V0_RESULTS.md](docs/EMOJI_WORD_INCONGRUENCE_REPLICATION_V0_RESULTS.md) | [EMOJI_WORD_INCONGRUENCE_REPLICATION_V0_RESULTS.ja.md](docs/EMOJI_WORD_INCONGRUENCE_REPLICATION_V0_RESULTS.ja.md) |
| E2 Stage-A3 numeric-screen results | [LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.md](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.md) | [LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.ja.md](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.ja.md) |
| E2 Stage-A3 numeric-screen protocol | [LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.md](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.md) | [LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.ja.md](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.ja.md) |
| E2 Stage-A v2 results | [LLAMA32_3B_MLX_VALIDATION_RESULTS.md](docs/LLAMA32_3B_MLX_VALIDATION_RESULTS.md) | [LLAMA32_3B_MLX_VALIDATION_RESULTS.ja.md](docs/LLAMA32_3B_MLX_VALIDATION_RESULTS.ja.md) |
| E2 Stage-A v2 protocol | [LLAMA32_3B_MLX_VALIDATION_PROTOCOL.md](docs/LLAMA32_3B_MLX_VALIDATION_PROTOCOL.md) | [LLAMA32_3B_MLX_VALIDATION_PROTOCOL.ja.md](docs/LLAMA32_3B_MLX_VALIDATION_PROTOCOL.ja.md) |
| E2 MPS transport v2 protocol | [LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.md](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.md) | [LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.ja.md](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.ja.md) |
| E2 MPS transport v1 preflight failure | [LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.md](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.md) | [LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.ja.md](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.ja.md) |
| Holdout status | [HOLDOUT_STATUS.md](docs/HOLDOUT_STATUS.md) | [HOLDOUT_STATUS.ja.md](docs/HOLDOUT_STATUS.ja.md) |
| Reproducibility guide | [REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) | [REPRODUCIBILITY.ja.md](docs/REPRODUCIBILITY.ja.md) |
| Research roadmap | [ROADMAP.md](docs/ROADMAP.md) | [ROADMAP.ja.md](docs/ROADMAP.ja.md) |
| Phase I paper plan | [PAPER_OUTLINE.md](docs/PAPER_OUTLINE.md) | [PAPER_OUTLINE.ja.md](docs/PAPER_OUTLINE.ja.md) |
| Public research note | [NOTE.md](docs/NOTE.md) | [NOTE.ja.md](docs/NOTE.ja.md) |

Machine-generated artifacts, schemas, citations, licenses, and source code are exempt from line-by-line translation. English is the controlling language for the planned Phase I paper; the repository documentation remains bilingual.

## Historical Phase I goal and submission record

The following records the September paper-development stage. The current
standalone preprint and next-paper agenda are linked at the top of this README;
historical submission checks are not pending publication requirements today.

Phase I ends with an English preprint-ready paper supported by an auditable
evidence package. The [anonymous manuscript](output/pdf/glyphprobe_t19_first_draft.pdf)
combines T19's 9/9 token-count-matched lexical result, its symbol and component
boundaries, T20's calibration limits, and T21's conditional continuous-margin
contribution. The [v5 claim table](paper/CLAIM_TABLE.md) keeps these distinct.
The [paper package](paper/README.md) includes an anonymous artifact, licenses,
compute accounting, and ethics review. T19 primary-window statistics and T21
scalar inference can be replayed without models; the post-hoc T21 decomposition
remains descriptive. Raw-state replay, complete historical compute accounting,
and final author review remain limitations or pending work.

T15-B remains a separate prospective replication of an operational response-shape
candidate. These lanes do not establish human meaning, a complete mediator,
a universal circuit, tokenizer independence, a scale law, tuning invariance,
or model-population generality. Packaging and validation do not constitute
submission; final author approval and upload are separate. See the [T21 result](docs/T21_GLYPH_CONTEXT_PATH_RESULTS_V0.md),
[post-review audit](docs/POST_REVIEW_EVIDENCE_RESULTS_V0.md), and [roadmap](docs/ROADMAP.md).

T12 is also complete under its separate one-shot freeze. Its bounded result is
that neither the ZWJ fusion candidate nor the regional dual candidate met the
registered statistical-plus-practical rule. The T10 primary remains unchanged.
T13-EH completed a frozen exploratory acquisition over exposed items and
public targets; it did not alter the T12 decision or close a paper gate. Any T13-C
confirmation required a new untouched bank and a separate freeze; T14-C later
met that requirement without retroactively changing T13.
T13-EA has completed the corresponding exploratory point analysis without a
primary or confirmatory verdict. Its registered cluster bootstrap remains at
0/20,000. T14-X separately completed the expanded six-model response grid and
found a signed, non-monotonic model-by-depth regime. T14-C then completed one
prospectively selected-site causal experiment on a new untouched bank. Its
intersection-union test did not reject, so Phase I gate 4 is closed by a
negative result and no alternative site may be promoted from the same search.
T15-A then completed the four-model balanced interaction grid and found 16/16
positive primary response-coherence intervals, with heterogeneous secondary
families. T15-B prospectively replaced the axes, targets, and model roles and
supported its frozen two-model R1 intersection rule. Gate 5 is now satisfied
for that narrow operational candidate. Those historical decisions remain
unchanged by the later manuscript and T21 work described above.

## Validation

```bash
pytest
python -m compileall -q src/glyphprobe
glyphprobe matrix -x configs/backend_matrix.example.yaml --dry-run
```

Run IDs bind the resolved experiment inputs, implementation, runtime dependencies, model artifact identity, and parity receipt. Resume is permitted only inside the same sealed identity.

## License and citation

GlyphProbe is released under the Apache License 2.0. See [CITATION.cff](CITATION.cff) for citation metadata.
