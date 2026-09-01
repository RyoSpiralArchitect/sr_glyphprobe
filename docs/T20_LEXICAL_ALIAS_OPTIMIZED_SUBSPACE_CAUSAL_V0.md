# T20-C: Optimized-Subspace Causal Lexical Test (v0)

[日本語](T20_LEXICAL_ALIAS_OPTIMIZED_SUBSPACE_CAUSAL_V0.ja.md) | [T19 protocol](T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.md)

Protocol: `glyphprobe-t20-lexical-alias-optimized-subspace-causal-v0`
Config: [`configs/t20_lexical_alias_optimized_subspace_causal_v0.yaml`](../configs/t20_lexical_alias_optimized_subspace_causal_v0.yaml)
Runner: [`scripts/t20_lexical_alias_optimized_subspace_causal_v0.py`](../scripts/t20_lexical_alias_optimized_subspace_causal_v0.py)
Validator: [`scripts/validate_t20_lexical_alias_optimized_subspace_causal_v0_result.py`](../scripts/validate_t20_lexical_alias_optimized_subspace_causal_v0_result.py)

## Question

The registered T19-C test rejected one fixed rank-8 late-component account
under a low-baseline, single-context endpoint with no positive control. T20-C
asks the sharpened question that negative left open: **is there any rank-8
subspace at a late site, learnable by interchange optimization from the same
frozen source bank, that is jointly necessary and sufficient for held-out
glyph-to-alias retrieval — and was the test winnable at all, measured by a
full-representation interchange ceiling at the same site?**

## Exactly five deltas relative to T19-C

1. **Optimized construction.** The tested subspace is learned by gradient
   interchange training (InfoNCE toward the own-item alias plus a necessity
   hinge) on the frozen 128-item T19 causal-source bank, with a fixed 96/32
   train/validation split, three seeds, and a pinned seed-selection rule. The T19 closed-form cross-covariance rule and the deflated-span
   random control are computed at the same sites as comparators.
2. **Residual-stream sites.** `resid_out` at blocks 21, 24, 27 joins the six
   T19 component sites. Primaries are `resid_out@21` and `resid_out@24`
   (Holm over two). Block-27 residual is secondary: it is adjacent to the
   readout and its sufficiency is expected to be near-trivial.
3. **Component-gated decision.** Necessity and sufficiency are decided on the
   alias-retrieval component alone (adjusted against the random basis), with
   a codepoint self-retrieval guard (≥ 0.90 under the learned patch) so that
   representational disruption cannot pass as sufficiency. The T19 composite
   endpoint is still reported for continuity.
4. **Fresh, wider, multi-context evaluation.** 384 fresh atomic emoji with
   zero prior T19/T20 forwards, read in four contexts (pipe/article carriers ×
   distances 1 and 4), each context a 384-way retrieval. Per-item values are
   context means; the registered floor stays 0.02.
5. **Ceilings as positive controls.** Every site carries full-interchange
   conditions (glyph→codepoint and codepoint→glyph). The registered
   interpretation rule: a failed primary site whose sufficiency ceiling is
   below 0.06 is *uncalibratable at this endpoint*, not evidence against the
   low-rank account. No ceiling can flip a failed decision to positive.

## Item banks

- Source/training: the frozen T19 `causal_source_items` (128), verbatim.
- Evaluation: 384 fresh atomic emoji drawn by the frozen round-robin sampler
  from the unused remainder (579) of the byte-identically reproduced T19
  matching. Selection re-runs the frozen T19 builder on the hash-pinned
  Unicode 17.0 / CLDR 48.2 sources and requires the reproduction to equal the
  frozen T19 selection manifest SHA-256 before drawing a single fresh row.
- The non-emoji symbol pool is exhausted (55/55 consumed by T19) and carries
  no T20 arm.

## Gate sequence

1. `build-selection` — byte-identical T19 reproduction audit, fresh bank drawn,
   zero forwards.
2. `audit-design` / `tokenizer-preflight` — structural and tokenizer receipts,
   zero forwards.
3. `build-freeze` — SHA-256 manifest over config, selection, code, tests,
   docs, and both preflights. Commit and push; `audit-freeze --require-pushed`
   must pass.
4. `admit-go` — requires the validated T19-C analysis, the T19 freeze/go
   chain, the T20 freeze, and zero forward counters. The runner records its
   own SHA-256 and refuses to run if it changes afterward.
5. `run-training` — source capture (384 forwards) plus interchange training;
   source-bank forwards only.
6. `run-evaluation` — 32,256 evaluation forwards, 124,416 intervention rows,
   sealed with ledgers.
7. `analyze` → `validate-analysis` → independent validator.

## Decision

Per primary site: adjusted necessity and sufficiency means ≥ 0.02 with
bootstrap lower-95 bounds > 0.02, one-sided sign-flip p-values under Holm over
the two primaries, self-retrieval guard ≥ 0.90, and exact zero-hook and
remove-restore engineering checks. Verdicts are `positive`,
`negative_with_informative_ceiling`, or `uncalibratable_at_endpoint`.

## Claim boundary

See `claim_boundary` in the config. In particular: behavioral endpoints are
deliberately out of scope (the T16-OSC record covers forced-choice behavior);
no visual-perception, human-meaning, uniqueness, completeness, scale, or
model-population claim is authorized by any outcome.
