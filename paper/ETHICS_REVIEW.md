# Ethics and responsible-release review

[日本語](ETHICS_REVIEW.ja.md)

Status: **author-side review completed on 2026-09-02** against the
[NeurIPS Code of Ethics](https://neurips.cc/public/EthicsGuidelines). This is a
scope-specific self-audit, not an institutional legal or IRB determination.

## Scope review

| Area | T19 finding | Mitigation or boundary |
|---|---|---|
| Human participants and crowdsourcing | None. | No recruitment, instructions, compensation, intervention, or IRB-triggering participant procedure exists. |
| Privacy and personal data | None. | Inputs are public Unicode scalars, standardized English annotations, literal codepoint strings, and fixed carrier tokens. No user messages, accounts, identifiers, or scraped personal content are used. |
| Data and model terms | Reviewed. | Model weights are obtained under their upstream terms and are not redistributed. Qwen2.5 3B is used only for non-commercial research. Unicode-derived rows travel with the Unicode License v3 notice. See `ASSET_LICENSES.md`. |
| Representativeness | Material limitation. | CLDR English annotations are standards metadata, not universal human meanings, familiarity ratings, or population samples. The paper forbids cultural, sentiment, and identity generalization. |
| Scientific integrity | Controlled. | Frozen endpoints, item banks, negative results, failed prior confirmations, multiplicity rules, practical floors, and raw-data omissions are retained explicitly. The archive never upgrades hash integrity into scientific correctness. |
| Misuse | Low capability risk, non-zero interpretive risk. | The work releases no new model or operational steering capability. The principal risk is unjustified profiling or cultural inference from lexical correspondence; the paper expressly rules out that use. |
| Environmental impact | Finite inference-only experiment; exact impact unknown. | No training was performed. Forward counts are reported, but duration, energy, and carbon were not receipt-bound and are not estimated after the fact. |

## LLM-assistance disclosure

LLM coding and research assistants supported protocol drafting, code
generation, manuscript editing, and one author-side fresh-eyes review. They did
not supply CLDR labels, label experimental items, choose outcomes after seeing
T19 results, or serve as the scientific evaluator. The authors retained
execution authority and approved the frozen endpoints, banks, and final claims;
numerical outputs and independent validators were checksum-bound. Assistant
prose and suggestions were treated as untrusted drafts and checked against the
frozen evidence.

This disclosure is conservative: assistant use affected the research workflow
even though no assistant output is an experimental measurement.

## Conclusion

Within the declared scope, T19 conforms to the reviewed NeurIPS ethics
principles: it uses licensed public resources, avoids human and personal data,
preserves adverse evidence, and states the principal representational and
misuse risks. The remaining compute-accounting gaps are disclosed in
`COMPUTE_REPORT.md`; they are transparency limitations, not concealed values.
