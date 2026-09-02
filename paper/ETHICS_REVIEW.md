# Ethics and responsible-release review

[日本語](ETHICS_REVIEW.ja.md)

Status: **author-side review completed on 2026-09-02** against the
[NeurIPS Code of Ethics](https://neurips.cc/public/EthicsGuidelines). This is a
scope-specific self-audit, not an institutional legal or IRB determination.

## Scope review

| Area | T19/T20/T21 finding | Mitigation or boundary |
|---|---|---|
| Human participants and crowdsourcing | None. | No recruitment, instructions, compensation, intervention, or IRB-triggering participant procedure exists. |
| Privacy and personal data | None. | Inputs are public Unicode scalars, standardized English annotations, literal codepoint strings, and fixed carrier tokens. No user messages, accounts, identifiers, or scraped personal content are used. |
| Data and model terms | Reviewed. | Model weights are obtained under their upstream terms and are not redistributed. Qwen2.5 3B is used only for non-commercial research. Unicode-derived rows travel with the Unicode License v3 notice. See `ASSET_LICENSES.md`. |
| Representativeness | Material limitation. | CLDR English annotations are standards metadata, not universal human meanings, familiarity ratings, or population samples. The paper forbids cultural, sentiment, and identity generalization. |
| Scientific integrity | Controlled. | Prespecified endpoints, item banks, negative results, failed prior confirmations, multiplicity rules, practical floors, and raw-data omissions are retained explicitly. T21-C's new margin endpoint and positive result are separated from unchanged T19/T20 top-1 verdicts. The archive never upgrades hash integrity into scientific correctness. |
| Misuse | Low capability risk, non-zero interpretive risk. | The work releases no new model or operational steering capability. The principal risk is unjustified profiling or cultural inference from lexical correspondence; the paper expressly rules out that use. |
| Environmental impact | Finite experiments; exact impact unknown. | Model weights were never trained; T20-C optimized small subspace parameters. Forward counts and T20/T21 stage times are reported. Missing T19 times, peak memory, energy, and carbon are not estimated after the fact. |

## LLM-assistance disclosure

LLM coding and research assistants supported sequential protocol development,
code generation, analysis, manuscript editing, and an author-side fresh-eyes
review. The T21 question was developed after T20 and a declared exposed-item
pilot; its confirmation endpoint and rules were recorded before accessing
the 195 remaining items. Labels came from CLDR, and assistant judgments were
not experimental measurements. The authors retained execution authority and
responsibility for final claims. Numerical outputs and independently
implemented validators were checksum-bound; this is not an external
replication or a substitute for author review.

This disclosure is conservative: assistant use affected the research workflow
even though no assistant output is an experimental measurement.

## Conclusion

Within the declared scope, T19/T20/T21 conform to the reviewed NeurIPS ethics
principles: it uses licensed public resources, avoids human and personal data,
preserves adverse evidence, and states the principal representational and
misuse risks. The remaining compute-accounting gaps are disclosed in
`COMPUTE_REPORT.md`; they are transparency limitations, not concealed values.
