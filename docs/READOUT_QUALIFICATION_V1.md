# Explicit-report readout qualification

[日本語](READOUT_QUALIFICATION_V1.ja.md)

Protocol date: October 15, 2026. Prospective finite-set development experiment,
specified before its model scores. This is an internal specification, not an
external preregistration. No historical endpoint, result, or participant record
is changed. Public release and DOI registration are separate actions.

## Question and contribution

For the same Llama 3.2 3B base checkpoint and matched-execution scorer, which
response failures persist when question embedding and answer encoding change,
while the explicit report and queried proposition remain fixed? The earlier
contextual experiment failed explicit completion controls. This follow-up tests
the measurement on new, stipulated text-only facts, without assuming an emoji
meaning or treating a model's preferred continuation as a human judgment.

## Fixed inventory

- 32 new fact roots, four source-defined domain/template families, eight roots
  per family. Two whole families (16 roots) are development material; two other
  families (16 roots) are reserved-check material. Both inventories and all
  analyses are fixed before any forward. There is no tuning after development.
- Three report states: explicit P, explicit not-P, or unknown. Each report is
  queried about P and not-P. The target is what the report explicitly states,
  not what actually happened. Unknown supports neither assertion; it is never
  coded as an explicitly false event.
- Three question forms: `Does the report explicitly state that {proposition}?`,
  `Is it true that the report explicitly states that {proposition}?`, and
  `Is it false that the report explicitly states that {proposition}?`.
  The last reverses the expected answer to the same evidence proposition.
- Four answer formats: historical full Yes/No sentences, minimal Yes/No,
  A/B with A meaning Yes, and A/B with A meaning No. Each arbitrary mapping is
  explicitly stated. The two mappings retain the same displayed label order.
- 32 × 3 × 2 × 3 × 4 = **2,304 candidate pairs / 4,608 scientific sequence
  forwards**, plus 32 historical sentinel forwards = **4,640 maximum**.
  Rows are repeated measurements of 32 roots and four template families,
  not 2,304 independent tasks.

Exact prompts, mappings, logical references, token IDs, source hashes, model
files, runtime, and the complete schedule are bound by the prepared specification.
No protected historical bank, old private questionnaire, or CLDR target is read.

## Decisions fixed before execution

1. Numerical acceptance requires every scheduled row, valid token boundaries,
   finite token sums, exact same-prefix scores, and exact initial/final historical
   sentinels. Predictor-logit equality includes the first divergent answer-token
   position; zero shared answer tokens cannot pass by an empty comparison alone.
2. **Primary finite-set gate:** the direct question with minimal Yes/No must be
   correct on all **96 reserved-check cases** (16 roots × three reports × two
   assertions), with zero ties and 16/16 roots correct on all six cases.
   This demanding operational threshold is chosen because the facts and support
   rule are explicit. It is neither a population accuracy estimate nor a threshold
   calibrated to semantic understanding.
3. **Separate label-robustness gate:** both arbitrary mappings of the direct
   question must be correct on all **192 reserved-check cases**, with zero ties.
   Agreement between two wrong answers does not pass. A primary pass together
   with a mapping failure qualifies only the fixed minimal Yes/No format.

All formats and failures are reported; no best-format selection or replacement
of the historical estimator is permitted. No p-values or population intervals
are introduced. Any optional later emoji transfer requires a separate decision;
it is not included in this acquisition and cannot become fresh scenario N.

## Analysis and limitations

Report complete planned/completed/failed denominators; correctness and margins
by split, family, report state, queried assertion, question, and encoding;
class-balanced accuracy; all-six-cases/root success; ties; decoded mapping
agreement and correctness; and direct/nested and true/false consistency.
Direct support prevalence is one third, so constant No scores two thirds raw
accuracy and one half class-balanced accuracy. This baseline must remain visible.
Full-sequence and first-divergent-token scores are separate estimators; the
remaining continuation contribution is reported rather than discarded.

Label mapping adds instruction-following demands. Answer formats vary wording
and scored suffix, so differences do not identify punctuation as a cause.
Question forms vary linguistic demands; this is not a neural intervention.
Explicit support can be solved by literal matching and passing is insufficient
for contextual interpretation. The reserved templates are source-authored,
not independently human-validated. No emoji specificity, cross-model result,
free generation, new mechanism, or independent human confirmation is claimed.

## Execution and stopping

Use the existing pinned BF16 Transformers/CUDA eager-attention runtime and
checkpoint, with no chat template, download, training, or generation. This
exact-logit/replay experiment requires that historical implementation; changing
to the host's general-purpose TensorRT generation service would change the
measurement and invalidate sentinel comparisons. No managed environment is
modified. Candidate pairs have equal padded shape and the same FP32
normalization rectangle; only real continuation tokens are summed.

Check occupancy before loading and before/after every forward. Other GPU
processes block execution; stop on contention and preserve every planned
missing row. Maximum wall time is 1,800 seconds; Torch allocator cap 9,728 MiB
plus 512 MiB driver allowance. Require 12,288 MiB free before load and 4,096 MiB
at forward boundaries. No automatic retry, peer-process modification, or silent
runtime fallback. Run in an isolated furnace checkout. Analyze saved scores on
CPU and independently verify aggregates before manuscript integration.
