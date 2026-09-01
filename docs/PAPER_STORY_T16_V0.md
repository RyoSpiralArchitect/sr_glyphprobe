# T16 paper story v0

[日本語](PAPER_STORY_T16_V0.ja.md) · [Integrated claim table](../validation/t16_integrated_v0/claim_table.json) · [T16-UTF-X1 stress test](T16_UTF_SCALE_VARIANTS_V1_RESULTS.md) · [Phase I outline](PAPER_OUTLINE.md)

Status: **submission-story draft, not the final manuscript claim freeze**.

## Working title

**Behaviorally Legible, Mechanistically Unresolved: Separating Emoji Fingerprints, Congruence, and Causal Mediation**

Alternatives:

1. **From Glyph Fingerprints to Operational Semantics: Causal and Unicode Controls for Emoji Representations**
2. **Emoji Representations Are Behaviorally Legible but Not a Single Causal Circuit**
3. **When an Emoji Fingerprint Is Not a Meaning Circuit**

The first title is the safest. It states the dissociation without converting a
negative sufficiency result into evidence for a particular distributed circuit.

## One-sentence thesis

Reproducible emoji-conditioned response fingerprints and successful
forced-choice emoji-word judgments do not identify the same causal object:
operational behavior is legible, but the tested fingerprint subspace and late
mediator band fail stronger causal implementation tests, while exact-string
controls reveal a separate tokenizer-conditional geometry of repetition and
Unicode-family diversity.

## Draft abstract

Emoji offer compact probes of language-model representations, but their visual
salience, Unicode composition, tokenization, and learned associations make
semantic and mechanistic interpretations easy to overstate. We separate four
levels of evidence. First, an emoji-word interaction fingerprint discovered in
four models prospectively recurred across eight new axes, 48 new targets, and
two new model roles. Second, in separately frozen two-alternative tasks, Gemma
2 2B IT and Mistral 7B Instruct v0.3 both selected experimenter-assigned emoji
meanings and distinguished congruent from incongruent emoji-word pairs; all
four model-by-task gates passed. Third, the residualized replicated fingerprint
did not causally support explicit mismatch judgment in Mistral: treatment,
sufficiency, and necessity estimates were non-positive in the registered
orientation. In a separate Llama 3.2 3B steering endpoint, a jointly patched
eight-component late band passed its necessity component but failed
sufficiency and the full mediation intersection test. Finally, exact-UTF
controls across six Unicode construction families separated repeated-string,
within-family, and cross-family displacement: cross-family excess was positive
at all eight tested model-by-depth cells, but remained tokenizer-conditional.
An exploratory 515,808-record stress test extended the sign through `n=500`
in 36/36 fixed model-by-depth cells and found that contiguous item blocking
maximized displacement in 72/72 nearly token-multiset-exact order cells, while
the length curves remained non-monotonic. These results show that response
fingerprints, operational semantic behavior, causal implementation, and
Unicode-conditioned sequence geometry are distinct empirical layers. Emoji
behavior is measurable; its mechanism remains distributed or unresolved
rather than localized by the tested routes.

## The paper's actual contribution

The paper is not strongest as “we found an emoji circuit.” The stronger and
more defensible contribution is a **claim ladder with empirical separations**:

```text
reproducible output fingerprint
             ↓ does not entail
forced-choice semantic behavior
             ↓ does not entail
causal implementation by that fingerprint
             ↓ does not entail
local or sufficient late-layer mediation
```

GlyphProbe contributes a fail-closed way to climb that ladder without silently
renaming evidence from one level as evidence at the next. The negative causal
results are central, not an embarrassment: they demonstrate why the levels
must be tested separately.

## Evidence spine

| Layer of evidence | Study | Result | Authorized reading |
|---|---|---|---|
| Response fingerprint | T15-B | Prospective two-model R1 support: SmolLM2 `+0.020422` [0.012887, 0.031510]; Mistral `+0.060397` [0.056621, 0.062194] | A narrow response-shape contrast recurs under new axes, targets, and roles |
| Operational association | T16-OSC behavior | Meaning accuracy `0.9531` Gemma, `0.9375` Mistral; both gates pass | Frozen two-choice emoji-word association is legible |
| Operational congruence | T16-OSC behavior | Congruence accuracy `0.7617` Gemma, `0.7539` Mistral; both gates pass | Frozen matching versus mismatching judgment is legible |
| Fingerprint-to-behavior causality | T16-OSC causal | Treatment `-0.1484`, sufficiency `-0.0859`, necessity `-0.0547`; gate fails | The T15-B subspace is not the validated implementation of explicit mismatch judgment |
| Late-band mediation | T16-DP | Necessity `+0.000871` passes; sufficiency `-0.000146` fails; treatment misses floor | The complete late band carries a necessary component but is not sufficient under transplantation |
| Exact-string geometry | T16-UTF | Cross-minus-within interval positive in 8/8 model-depth cells | Repetition and construction-family diversity separate conditionally on tokenizer paths |
| Long-sequence and order stress | T16-UTF-X1 | Primary and `n=500` cross-minus-within positive in 36/36 cells; blocked order largest in 72/72 cells | The conditional geometry persists on this fixed roster; exact-token-multiset order affects state, but no scale law or Unicode semantics follows |

## Main narrative by section

### 1. Introduction: an emoji creates four confounds at once

An emoji is visually compact but computationally untidy. It carries a familiar
human association, a Unicode construction, a tokenizer path, and a model-state
perturbation. Prior work often jumps from the last item to the first. We ask
what survives when these layers receive separate endpoints and causal tests.

### 2. Measurement: establish a stable response object

Summarize T15-A briefly and make T15-B the measurement anchor. The important
advance is not the raw row count; it is that every axis, target, and model role
was replaced before the frozen R1 analysis. Keep the six-positive/two-mixed
primary-dose cells visible. This establishes a reproducible object worth
testing, not meaning.

### 3. Operational semantics: ask the model directly, narrowly

Introduce the independent eight-axis panel and counterbalanced `A`/`B`
surfaces. Report logit-margin inference and accuracy together. Describe the
result as association and congruence judgment. The phrase “meaning
understanding” should appear only in the limitation that this task does not
establish it without restriction.

### 4. Causal dissociation: the replicated fingerprint is not the judgment

This is the paper's hinge. Explain how the true interaction direction was
residualized against seven cross-axis interactions and emoji/word main effects.
Then show all three estimates on one signed axis. Their negative orientation is
more informative than a generic non-significant result: the source fingerprint
and the explicit mismatch endpoint are not interchangeable causal variables.

### 5. Distributed route: necessary information without sufficiency

Use T16-DP as a separate mechanistic boundary, not as a rescue of T16-OSC. The
complete block-24–27 attention-plus-MLP band lost treatment information when
reset to baseline, yet could not recreate the effect when transplanted. State
the joint IUT failure first. “Necessary but not sufficient under this patching
operation” is acceptable; “the circuit is distributed” is a hypothesis unless
carefully qualified.

### 6. Unicode side control: representation is not only semantics

Move T16-UTF to the last main result if space permits, otherwise to the
appendix. The exact `n=1` identity is an unusually clean internal control.
Cross-family excess at all depths is interesting because the profile differs
between Gemma and Mistral, but token-count-matched cross-family subsets are
sparse. Treat this as geometry that motivates future tokenizer-matched causal
controls, not as a semantic decomposition.

Use T16-UTF-X1 as an appendix stress test, not as a fifth rung in the causal
claim ladder. Its useful addition is a separation inside sequence geometry:
cross-family excess stays positive through `n=500`, but it is non-monotonic;
meanwhile, preserving the exact item multiset and almost always the exact
token multiset still leaves a strong order effect, with contiguous blocking
largest in all 72 cells. Keep the separator result subordinate because none of
those pairs preserve the token multiset.

### 7. Discussion: three separations, one method lesson

The discussion should close around three separations:

1. reproducibility versus semantics;
2. operational semantics versus causal implementation;
3. UTF identity versus tokenizer-independent composition.

The method lesson is that negative causal tests can increase explanatory
resolution. They prevent a reliable observational fingerprint from absorbing
claims it did not earn.

## Figure and table plan

### Main figures

1. **Claim ladder and experimental split.** One schematic linking T15-B,
   T16-OSC behavior, T16-OSC causal, and T16-DP, with red “does not entail”
   arrows.
2. **Behavior-to-causality dissociation.** Left: four behavioral axis-median
   intervals. Right: three signed causal estimates, all at or below zero.
3. **Joint late-band patching.** Intervention diagram plus the three IUT
   components and practical floors.

### Main table

One compact claim table should list the endpoint, principal sampling unit,
multiplicity rule, outcome, and maximum authorized claim for T15-B and T16.

### Appendix figures

- T16-UTF cross-minus-within heat map by model, depth, and `n`.
- Clone, within-family, and cross-family displacement profiles.
- Per-construction-family heterogeneity and exact-token-count subset counts.
- T16-UTF-X1 blocked-versus-shuffled order profiles and anchor-position
  profiles, with token-multiset match rates printed beside each panel.
- Full T15-B secondary heterogeneity and the preserved zero-guard failure.

## Five-page fallback

If the body must fit five pages, keep only:

1. the T15-B prospective replication paragraph;
2. the T16 behavioral result;
3. the T16 causal sign reversal;
4. the T16-DP necessity/sufficiency split;
5. one limitations paragraph.

Move T16-UTF, T16-UTF-X1, detailed T15 history, per-axis values, and engineering
receipts to the appendix or repository. The paper remains coherent without the
UTF results; it does not remain coherent without the behavioral-to-causal
dissociation.

## Claims to freeze before submission

### Safe central claims

- A prospectively replicated emoji-word response-shape fingerprint exists in
  the tested cells.
- Frozen two-choice emoji-word association and congruence judgments succeed in
  two instruction-tuned model cells.
- The tested T15-B residual subspace does not implement the explicit mismatch
  endpoint in its registered orientation.
- A separately tested late band has a positive necessity component but fails
  sufficiency and the full mediation gate.
- Cross-family mixing adds tokenizer-conditional displacement beyond
  within-family mixing in all eight descriptive cells.
- In the exploratory stress-test roster, that sign remains positive through
  `n=500`, while exact-token-multiset order changes the captured state. This is
  an appendix-level robustness claim, not a scale or semantic claim.

### Claims the manuscript must not make

- unrestricted emoji meaning understanding;
- general contradiction detection;
- a unique, minimal, complete, or model-general emoji circuit;
- tokenizer-independent Unicode composition;
- a scale law or architecture law;
- confirmation status for outcome-informed causal follow-ups;
- equality of hidden-state magnitude across models.

## Submission-day editing order

1. Freeze the claim table and abstract wording.
2. Build Figure 2 first; it carries the central dissociation alone.
3. Write Results around the frozen tables, not chronologically around every
   experiment.
4. Add Methods sufficient to reproduce principal units, gates, and repairs.
5. Put negative cells, outcome-informed status, and tokenization limits in the
   body before compressing prose.
6. Run a final blind-claim and evidence-link audit; polish only after those
   checks pass.

The current repository evidence is sufficient for a complete draft. It is not
yet a final camera-ready claim freeze, and the paper should preserve that
distinction until the figure values and manuscript tables are regenerated from
the committed compact analyses.
