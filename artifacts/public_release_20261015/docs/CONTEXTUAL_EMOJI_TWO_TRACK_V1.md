# Two questions about contextual cues: development version 1

[日本語](CONTEXTUAL_EMOJI_TWO_TRACK_V1.ja.md)

## Purpose and status

This prospective **development** specification is written after the author pilot
and its disclosure. It separates bounded state matching from interpretation in
ordinary-looking messages. The same 24 scenarios and six families are reused;
new prompt variants are not new independent observations. No independent human
validation, confirmatory success, or causal conclusion is claimed. Original
materials, author responses, and previous results remain unchanged.

## Two tracks and three propositions

| Track | Question | Assumption and boundary |
| --- | --- | --- |
| Bounded state match | Does the reported property match the explicitly requested property? | The report is accurate about that property; cue meaning can still be unclear. |
| Naturalistic message reading | Does the message suggest the stated property or affect? | No added guarantee of truth or practical success. |
| Naturalistic outcome evidence | Does this message alone establish a specified wider outcome? | A setting, forecast, plan, or proposal can convey something without establishing execution. |

Every proposition has a Yes/No answer. In the human workbench, a **separate,
required Yes/No assessability question** first asks whether the reader can decide.
If not, the proposition answer stays null, never No. Unclear language and reasons
for missing context are recorded separately. These are structured judgments,
not unrestricted conversation or independent gold labels.

The affect family deliberately differs across tracks: the bounded question is
about a visible smile/tears, while the naturalistic question concerns expressed
pleasure/sadness. For other families, practical goals are narrowed to temperature,
setting, status, direction, or forecast category. Track differences therefore do
not isolate an instruction-only causal effect. The full rewriting inventory must
remain available, including difficult families.

## Model acquisition, fixed before its outputs

One existing offline Llama 3.2 3B BF16 model is used with the previously qualified
eager-attention, equal-shape scorer. No model download or generation is required.

- 24 scenarios × 2 contexts × (2 emoji + 2 words + 1 absent-cue control)
  × 3 propositions × 2 question polarities = **1,440 candidate pairs**.
- For outcome evidence, two additional text-only anchors per context explicitly
  give an accurate completed-outcome report or state that the outcome is unknown:
  24 × 2 × 2 × 2 polarities = **192 pairs**. These are logical calibration
  anchors, not emoji conditions and not a discovery of communication semantics.
- Total: **1,632 pairs / 3,264 candidate sequences**, plus 32 old exact-replay
  sentinel forwards = **3,296 forwards maximum**. Independent scenario N remains 24.
- Candidates are always ` The answer is yes.` and ` The answer is no.`.
  Positive “Is it true that …?” and negative “Is it false that …?” questions
  are both retained. This is a polarity sensitivity check, not extra evidence N.
- The local tokenizer is called before acquisition. Literal strings, token IDs,
  source hashes, model files and runtime identity are saved in the specification.
  Candidate boundaries must preserve the prompt token prefix exactly.
- Pad both sequences to the same length, normalize the same FP32 rectangle,
  and gather valid continuation tokens only. Common continuation-prefix logits
  and probabilities must agree exactly. Saved original sentinels must replay
  exactly at the start and end. Failed gates retain all planned missing rows.
- Before loading and before/after every forward, reject other GPU PIDs; require
  12 GiB free before loading and 4 GiB at forward boundaries. Torch allocation
  cap is 9.5 GiB plus 0.5 GiB driver allowance; wall time is at most 30 minutes.
  Yield on contention; no automatic retry or peer-process change.

Reports will retain all carriers, families, questions, polarities, anchors,
missingness, exact token sums, prefix checks, and polarity disagreements. Report
within-question Yes-minus-No sequence log probabilities and the original
two-context/two-cue difference of differences as descriptive model behavior.
No p-values, retrospective thresholds, human accuracy, “emoji superiority,” or
automatic replacement of manuscript numbers are authorized by this development run.
Absent-cue controls are shared across cue alternatives and are not duplicated N.

## Workbench and human gate

The next author tryout has 24 unique scenarios, one view each: 12 bounded and
12 naturalistic, with 12 emoji and 12 words. Each family has one item in each
track-by-carrier cell. Context/cue combinations occur once per family. Assignment
uses a fixed source-only seed before new model outputs and never uses response
agreement. The 12 bounded items have one substantive question and the 12
naturalistic items have two, giving 36 substantive judgments. Both naturalistic
questions are visible on one page; interpretive priming remains a limitation.

The interface retains the plain white, blue-accented reading layout of v0:
one vignette, clearly separated questions, Yes/No controls, optional reasons and
note, and explicit save/review/finalize. No generated imagery is used, as requested.
Record research familiarity, prior model-result exposure, prior response/key
comparison exposure, English confidence, and optional item recognition separately.
The author is already exposed; a self-report never overrides this known history.
No correct answer or model result is shown. Files stay local, outside Git and
outside shared storage. Existing v0 files and its running server are not changed.

Larger independent validation remains a separate gate: an independent evaluator,
new independently prepared scenarios, a pre-response analysis rule, and a plan
for uncertain judgments. This tryout can improve usability and wording, but cannot
establish human validity or select favorable families for a confirmatory claim.

## Reproduction

`scripts/contextual_emoji_two_track_v1.py inventory --output PATH` writes the
model-free inventory. `package --output PRIVATE_DIRECTORY` writes a private,
source-only participant packet. Neither action reads human answers or model scores.
The separate runner prepares tokenization, then runs only from its saved specification.
No push, public release, recruitment, manuscript update, or training is included.
