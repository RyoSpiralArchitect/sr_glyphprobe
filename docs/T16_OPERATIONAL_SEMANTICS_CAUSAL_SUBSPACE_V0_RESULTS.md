# T16 operational semantics and causal subspace result

[日本語](T16_OPERATIONAL_SEMANTICS_CAUSAL_SUBSPACE_V0_RESULTS.ja.md) · [Frozen protocol](T16_OPERATIONAL_SEMANTICS_CAUSAL_SUBSPACE_V0.md) · [Closeout](../validation/t16_operational_semantics_causal_subspace_v0/closeout.json)

## Result in one paragraph

The behavioral lane passed all four frozen model-by-task gates. Across eight
new axes, Gemma 2 2B IT and Mistral 7B Instruct v0.3 both selected the
experimenter-assigned word for an emoji and distinguished matching from
mismatching emoji-word pairs in counterbalanced next-token choices. The
causal lane did not pass. A nuisance-residualized version of the prospectively
replicated T15-B interaction direction moved the explicit mismatch endpoint in
the opposite direction from the registered hypothesis: treatment, sufficiency,
and necessity medians were all non-positive. The combined result is a
mechanistic dissociation. The tested models expose operationally legible
emoji-word associations, but the T15-B response fingerprint is not their
validated causal implementation of explicit congruence judgment.

## Behavioral result

The principal unit was one semantic axis. Every cell used eight axes, a
20,000-replicate axis bootstrap, and an exact one-sided eight-axis sign-flip
test with Bonferroni alpha `0.0125`.

| Model | Frozen task | Axis median | 95% interval | Exact p | Forced-choice accuracy | Gate |
|---|---|---:|:---:|---:|---:|---|
| Gemma 2 2B IT | meaning choice | 9.156250 | [8.781250, 10.031250] | 0.00390625 | 0.953125 | pass |
| Gemma 2 2B IT | congruence judgment | 5.828125 | [3.062500, 6.750000] | 0.00390625 | 0.761719 | pass |
| Mistral 7B Instruct v0.3 | meaning choice | 14.531250 | [13.625000, 15.531250] | 0.00390625 | 0.937500 | pass |
| Mistral 7B Instruct v0.3 | congruence judgment | 6.843750 | [3.937500, 8.343750] | 0.00390625 | 0.753906 | pass |

All 768 response rows were present. Both model roles completed before the
behavior outcome was opened, and generation calls remained zero. Passing this
lane supports only the frozen two-alternative association and congruence
tasks. It does not establish unrestricted emoji understanding or general
natural-language contradiction detection.

## Causal residual-subspace result

The Mistral T15-B directions at normalized depths `0.875` and `1.0` were
projected away from a frozen nuisance span: seven cross-axis interactions plus
the emoji and word main effects. The registered gate required positive
treatment, sufficiency, and necessity components together.

| Estimand | Axis median | 95% interval | Exact one-sided p | Component |
|---|---:|:---:|---:|---|
| treatment | -0.148438 | [-0.281250, -0.015625] | 0.9921875 | fail |
| sufficiency | -0.085938 | [-0.125000, -0.062500] | 1.0000000 | fail |
| necessity | -0.054688 | [-0.195312, 0.000000] | 0.9921875 | fail |

The baseline forced-choice accuracy was `0.609375`. All 5,376 causal response
rows were present. The maximum zero-hook logit error was exactly `0`, and the
maximum full-vector restoration RMS error was
`3.0351459960619062e-18`.

The signs matter. This was not merely a low-power null: the frozen source
orientation shifted the operational mismatch endpoint oppositely to the
registered prediction. That finding narrows the interpretation of T15-B. Its
replicated next-token response shape is real under its own endpoint, but it
must not be renamed a congruence circuit.

## Preserved fail-closed repair

The first causal attempt compared an intervention batch of size 21 with a
plain batch of size 1 in the zero guard. It stopped before scientific causal
outcomes were opened. The failure is preserved in the
[failure receipt](../validation/t16_operational_semantics_causal_subspace_v0/causal_zero_guard_failure_v0.json).
The repair changed only the plain comparison to the same batch shape, was
frozen in a separate manifest, and then passed the zero and restoration gates.

## Claim boundary

T16-OSC supports operational forced-choice association and congruence in two
pinned instruction-tuned model cells. It rejects the registered claim that the
tested T15-B residual subspace implements that explicit mismatch endpoint in
the frozen orientation. It does not establish unrestricted meaning,
natural-language contradiction detection, tokenizer independence, a unique or
complete circuit, or model-population generality.

## Evidence

- [Behavior analysis](../validation/t16_operational_semantics_causal_subspace_v0/results/behavior_analysis.json), SHA-256 `d479e413db5eda8f8df2c7cfde32375c078af6c95b0759a71459ee063f7e8dec`
- [Causal analysis](../validation/t16_operational_semantics_causal_subspace_v0/results/causal_analysis.json), SHA-256 `86cd6dede2164d5fec3e7a7c128e0de0c313bf80c168d3ecb5f9c516941ca5f8`
- [Closeout](../validation/t16_operational_semantics_causal_subspace_v0/closeout.json), including remote run roots, receipt hashes, manifests, and the repair boundary

Raw response ledgers and activation arrays remain in the recorded furnace
scratch roots. They were not copied into Git.
