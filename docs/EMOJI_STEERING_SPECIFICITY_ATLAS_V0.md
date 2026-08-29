# Emoji Steering Specificity Atlas v0 — T13 decision map

[日本語](EMOJI_STEERING_SPECIFICITY_ATLAS_V0.ja.md) · [T13-EH acquisition protocol](EMOJI_STEERING_SPECIFICITY_HARVEST_V0.md) · [T12 result](GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.md) · [Roadmap](ROADMAP.md) · [Phase I paper outline](PAPER_OUTLINE.md)

Status: **future-work option map; not a preregistration and not authorized for
confirmatory execution**.

This document deliberately keeps several clean landing patterns available.
The separate T13-EH protocol freezes an exploratory acquisition over already
exposed T11 items and public targets; it is not a T13 confirmation and does not
open a protected bank. No T13-C model forward, tokenizer pass over a protected
bank, target selection, endpoint selection, or threshold selection has been
performed. Furnace availability may change scheduling and shard size; it must
not change a scientific endpoint or decision rule.

## Why return to the original question now

The project began with a broad question: does steering with an emoji-derived
direction do anything distinctive? The evidence has progressively removed
several easy answers.

- Shared token structure can produce strong matched-slot recurrence and can
  carry it into a common suffix.
- Simple distance attenuation did not reproduce under its frozen conjunction.
- Matched glyph/name alignment can be large in one model and broadly positive
  across a larger roster without satisfying a practical cross-model rule.
- T11 found system-specific ZWJ and regional candidates, but T12 did not
  confirm either candidate in their complete untouched reserves.

The T12 negative result is therefore a reason to ask a better version of the
original question, not a reason to widen the glyph panel until something
passes. “Emoji-specific” must mean a residual intervention effect that remains
after explicit lexical, token-structural, rarity, position, and random-direction
alternatives have been tested.

## The question to freeze later

> Under fixed source prompts, intervention sites and magnitudes, carrier
> positions, target prompts, and random controls, does an emoji-derived
> direction change model behavior more selectively than meaning-matched word,
> decomposed Unicode, token-structure-matched non-emoji, and norm-matched null
> directions?

This asks about intervention specificity. It is distinct from the observational
question “are glyph and name activations close?” Both lanes are useful, but an
observational geometry result must not be described as steering.

## Source families

Every semantic concept selected for T13 should generate a model-specific,
preflighted source family:

1. **Emoji glyph** — the rendered Unicode sequence used as the candidate.
2. **Official-name text** — a normalized Unicode name or fixed human-readable
   label for the same referent.
3. **Decomposed form** — scalar components separated without the presentation,
   joiner, or regional fusion convention.
4. **Matched non-emoji Unicode** — symbols or sequences matched as closely as
   possible for token count, prefix/suffix pattern, position, and corpus rarity.
5. **Matched ordinary text** — a non-emoji phrase matched for token count,
   lexical frequency, and source-wrapper structure.
6. **Null directions** — zero, norm-matched random, and orthogonalized random
   directions generated without target outcomes.

Controls must be frozen separately for each tokenizer output class. A control
that is structurally matched for Qwen must not silently stand in for a
different Llama, Gemma, OLMo, SmolLM, or Mistral tokenization.

## What would count as distinctive

An emoji-specific candidate should satisfy all of the following in a new
confirmation design:

- a positive emoji-minus-best-matched-control primary effect on an untouched
  target bank;
- a prespecified practical floor, not only a small p-value;
- sign reversal when the intervention direction is negated;
- ordered dose response over fixed magnitudes without outcome-selected clipping;
- selectivity for the intended target family rather than a global logit or
  entropy shift;
- survival of exact token-count and declared prefix/suffix sensitivities;
- success in a prespecified number of model roles, with materially opposed
  roles retained; and
- correction over the complete registered source-family × endpoint hypothesis
  family.

Passing these conditions would support a bounded operational statement:
emoji-derived directions have intervention behavior not reproduced by the
declared controls in the fixed roster. It would still not establish human-like
emoji meaning, a unique circuit, tokenizer independence, or generality beyond
the tested population.

## Two sealed lanes

### Lane A — representation audit

Lane A is observational and relatively cheap. It asks where glyph, name,
decomposition, and matched controls align across depth, carrier, and model. It
uses no interventions or generations. Its purpose is to reject weak source
constructions before a behavioral grid, not to produce the steering claim.

The clean first atlas is a source-class × target-class selectivity matrix with
matched controls and fixed normalized depth fractions. ZWJ and regional flags
remain useful stress tests because their displayed form is constructed from
multiple code points, but their T12 outcomes cannot select the new endpoint or
threshold.

### Lane B — intervention specificity

Lane B is the causal-behavioral test. It compares scalar-balanced directions at
fixed sites, signs, strengths, prompts, and target scoring rules. Required
arms are emoji, official-name text, decomposed form, strongest eligible
non-emoji/token control, random, sign-flipped, and zero intervention.

Generation can be a secondary blinded readout, but the primary endpoint should
be a deterministic paired score over a sealed target bank. Free-form examples
may illustrate a registered quantitative result; they must not select the
result.

## Staging without contaminating confirmation

### T13-E — exploratory source and endpoint screen

- Use only a public exploratory target set already designated for reuse or a
  newly created exploratory set.
- Preflight all nine tokenizer roles before loading any model.
- Acquire the complete nine-model representation atlas in resumable shards.
- Run a bounded intervention pilot in three representative roles chosen before
  outcomes: one small base model, one 3B-class base model, and one 7B-class
  model.
- Report all source families, signs, strengths, sites, and models. Do not
  assign a confirmatory status.

### T13-C — one-shot specificity confirmation

- Create a new untouched target bank outside the exposed research context.
- Freeze the primary endpoint, practical floor, model roster, site and strength
  rules, control eligibility, stopping rule, and multiplicity family before
  any target tokenization or model forward.
- Do not reuse P2 or retired C1 v1.
- Expand to all nine frozen roles in one acquisition if the design and compute
  budget are accepted. Shard boundaries may follow furnace windows, but the
  complete roster remains the estimand.
- Open outcomes once, preserve every failed and heterogeneous cell, and forbid
  alternate-site or alternate-endpoint rescue.

T13-E may design T13-C, but it cannot contribute observations to the T13-C
test statistic.

## Competing explanations and clean landing patterns

| Outcome | Best current interpretation | Paper/future-work landing |
|---|---|---|
| Emoji exceeds every matched source and null with dose/sign controls | bounded emoji-source intervention specificity | strongest T13-C candidate; mechanism remains future work |
| Emoji and official-name text are equivalent, both exceed structural controls | shared lexical/referential route | informative non-speciality result; compare source efficiency |
| Emoji and matched non-emoji Unicode track each other | token structure, rarity, or orthography is sufficient | tokenizer-conditioned account; no emoji-specific claim |
| Only ZWJ/regional interactions remain | sensitivity to Unicode composition conventions | study joiner/regional construction, not generic emoji meaning |
| Effects are model-local or signs disagree | model-conditioned geometry | publish heterogeneity; do not average into generality |
| No arm clears its practical floor | bounded null for the tested steering design | negative result closes Phase I cleanly |

All six landings are publishable if selected before the corresponding outcomes
are opened.

## Compute-aware queue

The efficient order is:

1. finish tokenizer and artifact preflights with zero protected-target access;
2. freeze model-specific control eligibility and shard manifests;
3. acquire the nine-model observational atlas while the furnace is available;
4. run the three-role exploratory intervention pilot in small resumable blocks;
5. decide, before creating or opening a confirmation bank, whether T13-C is
   justified for the workshop paper or belongs entirely in future work; and
6. if authorized, run all nine T13-C roles without changing the registered
   estimand when contention interrupts scheduling.

This preserves momentum without allowing resource availability to become a
hidden model-selection or stopping rule.

## Workshop boundary

The current Phase I paper does not need T13-C to be complete. T10's frozen
negative replication rule, T11's discovery atlas, and T12's one-shot negative
confirmation form a coherent account of why token-matched controls, practical
floors, model heterogeneity, and untouched reserves matter. T13 can appear as
the next falsifiable experiment.

If a T13 exploratory result is added before submission, it must be labeled
post-T12 exploratory, use no protected bank, and leave the T12 interpretation
unchanged. A result that cannot be independently validated before the paper
freeze stays in future work.
