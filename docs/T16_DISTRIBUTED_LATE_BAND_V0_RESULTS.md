# T16 distributed late-band result

[日本語](T16_DISTRIBUTED_LATE_BAND_V0_RESULTS.ja.md) · [Frozen protocol](T16_DISTRIBUTED_LATE_BAND_V0.md) · [Closeout](../validation/t16_distributed_late_band_v0/closeout.json)

## Result in one paragraph

The prospectively frozen eight-component late band did not pass the joint
mediation gate. In Llama 3.2 3B, replacing treatment-run `attn_out` and
`mlp_out` at blocks 24–27 with their baseline captures removed a positive,
practically nontrivial portion of the T14 treatment effect. Transplanting the
same eight treatment captures into the untreated run, however, did not
recreate the effect. The treatment itself also fell short of its frozen
practical floor. The bounded result is therefore a necessary-component signal
without sufficiency under transplantation, not a localized or complete emoji
circuit.

## Frozen joint test

| IUT component | Target median | 95% interval | Practical floor | One-sided p | Component |
|---|---:|:---:|---:|---:|---|
| treatment | 0.001716701 | [0.001476628, 0.001895659] | 0.002000000 | 0.000010 | fail floor |
| necessity | 0.000870887 | [0.000754687, 0.001012641] | 0.000500000 | 0.000010 | pass |
| sufficiency | -0.000146485 | [-0.000183541, -0.000091606] | 0.000500000 | 1.000000 | fail |

The intersection-union decision is
`joint_late_band_iut_non_rejecting`. A positive necessity component cannot
rescue the failed sufficiency and treatment components.

## Execution and controls

- Model: Llama 3.2 3B, with the T14 intervention at `resid_post` block 23.
- Joint band: `attn_out` plus `mlp_out` at blocks 24, 25, 26, and 27.
- Fresh target bank: 192 rows in 12 strata; exact prompt overlap with the bound
  prior banks was zero.
- Response rows: 15,360.
- Maximum explicit-zero JS: `0`.
- Maximum restoration JS and logit RMS error: `0` and `0`.
- Bound T14 upstream sham: pass.

The whole band was frozen before outcomes. No module was ranked, removed, or
selected after inspection.

## Interpretation

The late band is compatible with carrying information required for the T14
effect to propagate: restoring baseline band activations attenuated treatment.
It is not an autonomous mediator under the stronger intervention test because
the captured band state was insufficient in an untreated trajectory. Possible
explanations include distributed state outside the band, path-dependent
interactions with earlier residual state, or an endpoint whose practically
relevant effect is smaller than the frozen floor. These are future hypotheses,
not conclusions from this bank.

## Claim boundary

The result does not identify an individually necessary component, a minimal
band, a unique route, a complete circuit, emoji meaning, generated behavior,
tokenizer independence, or model generality. A subset search on the same bank
would be an adaptive rescue and is not authorized.

## Evidence

- [Compact analysis](../validation/t16_distributed_late_band_v0/results/analysis.json), SHA-256 `4f7687feae462efd91845b0c58b80a596134e3dc5cfcf7ee9936a0b5e85f666f`
- [Closeout](../validation/t16_distributed_late_band_v0/closeout.json), including the target-bank and run-receipt hashes

Raw ledgers remain in the recorded furnace scratch root and were not copied
into Git.
