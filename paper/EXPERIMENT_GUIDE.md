# Experiment guide: from keyword retrieval to conditional intervention

[日本語](EXPERIMENT_GUIDE.ja.md)

The study asks what lexical information a text model can retrieve from a raw
Unicode emoji, then tests specific ways that information might affect its
hidden states. It does not measure rendered-image perception, human meaning,
or generated behavior. The reader names below explain the experiments; the
historical IDs remain unchanged in protocols and results.

## Four questions, four experiments

| Reader name | Historical ID | Question | Items and scope | Actual evidence and boundary |
| --- | --- | --- | --- | --- |
| **Keyword retrieval** | T19-L | Does a raw emoji retrieve its word-disjoint CLDR keyword better than its literal codepoint spelling? | 55 emoji; 55 non-emoji symbols as secondary controls; nine model/tokenizer configurations. Matched emoji pools contain 31–51 items, depending on tokenizer. | All nine configurations pass unrestricted and token-count-matched criteria; the registered three-of-four core result is positive, with partial-conjunction p = 0.0027. This establishes a bounded lexical correspondence, not synonym understanding or human meaning. |
| **Fixed-subspace intervention** | T19-C | Does removing or transferring a source-learned rank-8 component subspace pass joint necessity and sufficiency criteria? | 128 source emoji; 192 different evaluation emoji; one Llama 3.2 3B checkpoint; one context; attention/MLP outputs at blocks 21/24/27. | Neither primary block-24 site passes. Exact zero-hook/restoration controls verify execution, not scientific sensitivity. Full-state swaps added after the decision show weak keyword effects at the primary sites, limiting the negative interpretation. |
| **Optimized-subspace intervention** | T20-C | Can interchange training find a useful rank-8 subspace, and do full-state swaps provide an informative reference? | The same 128 source items, split 96/32 for training/validation; 384 new evaluation emoji; four contexts; the same checkpoint; nine component/residual sites. | Neither primary residual site passes; both are **uncalibratable at this endpoint**, not calibrated negatives against low-rank mediation. Their full-swap sufficiency effects are 0.02344 and 0.02539, below the registered 0.06 reference minimum. |
| **Attention-path intervention after readout reset** | T21-C | After replacing the readout state, do later messages from glyph positions affect keyword similarity beyond equal-count suffix controls? | An exploratory pilot reuses the 384 T20 items; confirmation includes all 195 remaining T19/T20-unused emoji. Two carriers and two donors are averaged within each item; n = 195. | All five simultaneous lower bounds are positive for cosine-margin effects. Absolute glyph-message decrement and restoration have zero mean top-1 effects. The result is conditional on the reset, source/gallery pool, donor rule, and checkpoint; it is not unconditioned necessity/sufficiency or behavioral steering. |

“Fixed” means that the closed-form, source-learned basis is held fixed during
evaluation; it is not an arbitrary hand-picked basis. “Optimized” means that
the basis is trained by interchange optimization, not that the method has
found an optimal or exhaustive explanation. A low-rank basis need not be
sparse, and failure of one rank-8 intervention family does not reject every
causal account.

## One running example

The existing design example U+1F923 has four text views:

| View | Text supplied to the tokenizer |
| --- | --- |
| Raw Unicode | `🤣` — the Unicode scalar U+1F923 itself |
| Literal codepoint | `U+1F923` — the ASCII spelling, not the scalar |
| Official CLDR name | `rolling on the floor laughing` |
| CLDR keyword | `lmao` |

The keyword shares no ASCII-alphanumeric word with the official name. This
does not make it a human-validated synonym: the labels may co-occur in training
data and may share tokenizer features. This is an illustration of the design,
**not a claim that this individual item passed any experiment**.

For example, the pipe carrier appends eight copies of ` |` separately to each
view: `🤣 | | | | | | | |`, `U+1F923 | | | | | | | |`, and so on. A readout at
distance 1 takes the hidden state at the first suffix token; distance 8 uses
the eighth. The model is not asked to print `lmao`. Instead, the analysis
compares hidden-state vectors against a keyword gallery. Keyword retrieval
uses nearest-neighbor item identity after per-view centering and row
normalization. The later path experiment instead measures own-keyword cosine
similarity minus the largest similarity to 128 fixed source keywords.

The progression is:

1. **Readable?** Does the raw-character view retrieve the matching keyword,
   relative to codepoint spelling, across the prespecified contexts?
2. **Removal and transfer?** Learn a rank-8 basis from separate source items.
   Remove those coordinates on a glyph forward, or transfer same-item glyph
   coordinates into a codepoint forward. Compare both operations with a
   same-rank random-subspace control. Removal and transfer are different
   intervention conditions, not two readings of one forward.
3. **Optimized and calibrated?** Train the subspace through the intervention,
   add residual-stream sites, and compare with whole-state swaps. T20 also
   decides on keyword top-1 alone and guards codepoint self-retrieval: losing
   codepoint identity must not masquerade as acquiring the keyword.
4. **Conditional path?** Replace the readout residual after block 21 with its
   codepoint-view counterpart. In later blocks 22–27, replace keys and values
   at selected past positions for the readout query only. Compare glyph-position
   disruption/restoration with equal-count suffix controls, while retaining
   the same reset in the reference conditions.

The last step asks what contributes **after a specified state replacement**.
It does not show that the same pathway is necessary or sufficient in an
otherwise intact model.

## What token-count matching controls

Each item has a signature consisting of glyph kind and the token counts of
its four views: `(kind, raw, official name, keyword, literal codepoint)`.
Matched analysis retains strata with at least two items sharing that exact
signature and permutes keyword correspondence only within a stratum.

This does **not** require the four views of one item to have the same count.
For illustration, two emoji with signature `(emoji, 2, 6, 2, 5)` can share a
stratum; the tuple is hypothetical, not the measured U+1F923 signature.
Matching controls the signature across items, not token identity, tokenizer
construction, training frequency, or semantic familiarity. Unrestricted and
matched analyses use different retained galleries, so their effect magnitudes
are not directly interchangeable.

The randomization test asks whether the fixed keyword mapping beats the
permitted keyword permutations. The codepoint term stays fixed; this is not
a paired significance test of keyword–codepoint equality. The registered
decision separately requires the observed keyword-minus-codepoint advantage.

## Why 0.02, and how much does the decision depend on it?

The prespecified T19 protocol declares a 0.02 floor: two percentage points in its
top-1 difference statistic. It does not supply a separate utility, human-meaning,
or power-based calibration for that number. T20 retains the floor while
changing its decision endpoint to keyword top-1 alone. Prospective specification
prevents choosing a favorable threshold after observing results; it does not
by itself justify the threshold scientifically.

The decision rules also differ. T19-L applies the floor to both observed
unrestricted/matched estimates; its bootstrap intervals are descriptive.
T19-C/T20-C require both intervention effects and their lower 95% bounds to
exceed the floor, along with the registered tests and controls. T21 uses a
different unit, cosine margin, and requires five simultaneous lower bounds
above zero. It makes no practical-effect-size claim; 0.02 must not be carried
over to that endpoint.

The following is **descriptive arithmetic from saved T19-L estimates**, with
the existing randomization tests held fixed. It is not a new confirmatory
analysis or a replacement threshold.

| Hypothetical top-1 floor | Configurations meeting both point-estimate floors and the existing model test | Core configurations | Three-of-four practical conjunction |
| --- | ---: | ---: | --- |
| 0.02 or 0.03 | 9/9 | 4/4 | holds |
| 0.04 or 0.05 | 8/9 | 4/4 | holds |
| 0.06 | 6/9 | 4/4 | holds |
| 0.07 | 5/9 | 3/4 | holds |
| 0.08 | 4/9 | 3/4 | holds |
| 0.09 | 2/9 | 1/4 | fails |

The all-nine statement survives through a floor of 0.036363636; the core
three-of-four conjunction survives through 0.082516340 (rounded). The stored
partial-conjunction p remains 0.0027 because changing this floor does not
change the stored randomization tests.

Conversely, reducing the intervention floor to zero would not make any saved
T19-C or T20-C site positive: every site has at least one lower bound at or
below zero and a site IUT p-value above 0.05. This does not cure calibration.
T20's separate 0.06 full-swap reference minimum was chosen from the smaller
T19 set; the T20 baseline keyword gap is only 0.03320. Lowering that reference
minimum after the fact would change an interpretation label, not establish a
successful intervention. Full-state swaps are useful reference interventions,
not proven universal upper bounds on subspace effects.

## Why blocks 21, 24, and 27?

The observational late window was inherited from T18 before T19 acquisition:
normalized depths 0.75, 0.875, and 1.0. The recorded resolution rule is
`min(L - 1, floor(fraction * L))`. For the 28-block Llama checkpoint, it gives
zero-based block indices 21, 24, and 27 — the 22nd, 25th, and 28th blocks.
This explains the indices; it does not establish a universal semantic stage.

T19 fixes block-24 attention and MLP outputs as primary and 21/27 as secondary.
The cited protocol records that commitment but provides no separate empirical
calibration showing block 24 to be the uniquely appropriate primary site.
T20 makes residual21/24 primary; residual27 is secondary because it is adjacent
to the readout, making its transfer effect an expected endpoint-consistency
check. T21 then selects anchor 21 from blocks 21/24 using the specified rule on the
already-exposed pilot, before the separate 195-item confirmation.

Saved depth summaries permit a descriptive check without new model forwards:
each of the three late depths individually retains all nine configurations
above the 0.02 point-estimate floor in both analyses. The smallest estimate
across configurations/components is 0.02045 at 0.75, 0.05000 at 0.875, and
0.03182 at 1.0. Each leave-one-late-depth-out average also remains above 0.02.
These checks do not transfer the primary p-value to individual or alternative
depth windows. Across the full saved grid, individual models peak at different
depths, including early blocks; the data do not show a common late onset.
No conclusion about intervention effects at untested depths follows.

## Where to inspect the evidence

- Protocol and matched-control definitions: [T19 config](../configs/t19_lexical_alias_unicode_control_v0.yaml), [T19 protocol](../docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.md), and [T19 results](../docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0_RESULTS.md).
- Threshold/depth arithmetic inputs: [model-cell estimates](../validation/t19_lexical_alias_unicode_control_v0/results/model_cell_results.json) and [saved depth profiles](../validation/t19_lexical_alias_unicode_control_v0/results/depth_profiles.json).
- Intervention decisions: [T19 site results](../validation/t19_lexical_alias_component_causal_v0/results/causal_site_results.json), [T20 protocol](../docs/T20_LEXICAL_ALIAS_OPTIMIZED_SUBSPACE_CAUSAL_V0.md), and [T20 site results](../validation/t20_lexical_alias_optimized_subspace_causal_v0/results/causal_site_results.json).
- Conditional path definition and limits: [T21 confirmation protocol](../docs/T21_GLYPH_CONTEXT_PATH_CONFIRMATION_V0.md), [T21 results](../docs/T21_GLYPH_CONTEXT_PATH_RESULTS_V0.md), and [compact confirmation result](../validation/t21_glyph_context_path_confirmation_v0/results/confirmation_result.json).

This guide changes no protocol, registered decision, generated receipt, or
historical claim. The defensible thread is lexical readability, the limits of
tested local low-rank accounts, and a conditional attention contribution to
lexical geometry — not a demonstration of human-like meaning.
