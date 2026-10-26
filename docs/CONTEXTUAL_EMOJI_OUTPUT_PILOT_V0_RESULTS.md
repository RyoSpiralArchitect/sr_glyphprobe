# Contextual emoji output pilot: development results

[日本語](CONTEXTUAL_EMOJI_OUTPUT_PILOT_V0_RESULTS.ja.md) | [Protocol](CONTEXTUAL_EMOJI_OUTPUT_PILOT_V0.md) | [Study plan](CONTEXTUAL_EMOJI_CAUSAL_TRANSFER_PLAN_V0.md)

**Public-integration note, October 26, 2026:** this dated note retains the original
study status. References to excluded handoffs, notebooks, specifications or
runtime records concern the author's local archive; the public checkout does
not supply a complete historical run. See the
[public integration scope](PUBLIC_INTEGRATION_SCOPE_20261026.md).

Status, 2026-10-07: **the first output-scoring development pilot is complete;
the proposed causal study is not complete**. Publication remains deferred until
the new study is completed and reviewed. No upload or DOI reservation occurred.

Follow-up: the separate [192-cell word comparison](CONTEXTUAL_EMOJI_WORD_CONTROL_V0_RESULTS.md)
has now completed. This report retains the original emoji-baseline scope and
its acquisition-time control status; those cells and results were not changed.

## What was measured

For each of 24 author-written scenarios in six families, two goal contexts were
crossed with two emoji. Two fixed candidate continuations were scored for each
input. An emoji-absent condition was also scored in both contexts. This gives
144 inputs and **288 candidate-sequence cells**, all completed without missing
or failed cells, using the existing Llama 3.2 3B base BF16 model.

The experiment scores complete continuations by teacher forcing; it does not
generate answers. It uses no CLDR keyword target, readout reset, or internal
activation intervention. Labels express the author's proposed interpretation,
not independently established human judgments. A stable emoji status cue can
interact with a changing goal; these scenarios do not establish a change in the
emoji's meaning.

Let `s(c,e)` be the log-probability difference between the same candidate A and
candidate B at every input. `Delta_p` and `Delta_q` are the respective changes
in that difference when emoji A is replaced with emoji B. The block's recorded
sign `eta` orients `H = eta * (Delta_q - Delta_p)` toward the author's hypothesis.
Units are natural-log units (nats). No p-value, confidence interval, or
population-generalizing claim is reported.

## Results and their distinct meanings

| Diagnostic | Observation | Interpretation limit |
| --- | ---: | --- |
| Positive goal-by-emoji interaction, `H > 0` | **23/24 blocks** | The replacement effect changes in the proposed direction. This need not reverse its sign or the preferred response. |
| Intended effect crossover, `eta * Delta_p < 0 < eta * Delta_q` | **12/24 blocks** | The emoji replacement effect reverses direction across contexts. This is not a reversal of the most probable candidate. |
| Candidate argmax agrees with the author's proposed label | **54/96 crossed inputs** | An additional post-acquisition diagnostic, not human-validated accuracy or free-generation performance. |
| All four candidate choices agree within a block | **0/24 blocks** | No block meets all four proposed absolute response preferences. |
| Equally weighted mean of the six family means of H | **1.3122693 nats** | A descriptive finite-inventory interaction, not a calibrated semantic effect size. |

The first two diagnostics were specified before acquisition. The absolute-choice
diagnostics were added after inspecting the scores to distinguish interaction
from response preference. They are explicitly exploratory. A tie is not an
aligned choice. The negative interaction (`direction_02`, H = −0.2226228) is
retained; no block was removed based on its result.

| Family | Blocks | Mean H (nats) | H positive | Intended effect crossover |
| --- | ---: | ---: | ---: | ---: |
| Thermal goal | 4 | 0.885255 | 4/4 | 3/4 |
| Sound goal | 4 | 0.822570 | 4/4 | 3/4 |
| Completion goal | 4 | 1.574031 | 4/4 | 0/4 |
| Affect-tone goal | 4 | 2.477807 | 4/4 | 4/4 |
| Direction goal | 4 | 0.218898 | 3/4 | 1/4 |
| Weather goal | 4 | 1.895054 | 4/4 | 1/4 |

The completion family makes the distinction especially clear: all four H values
are positive, while none has the intended effect crossover. All per-input
scores, including both absent-input scores, remain in the saved results.
Conversely, `thermal_01` has H = 1.107030 and an intended effect crossover, yet
candidate B is more probable in all four crossed inputs. Even an effect
crossover does not establish four-way response selection.

## What this supports, and what remains open

The implemented endpoint can detect context-dependent changes in the relative
probability of ordinary candidate continuations on this finite development set.
The pattern motivates further controlled testing. It does **not** yet establish
emoji-specific semantics, reliable task performance, natural usage, or an
internal causal route. There are six recurring families and one candidate pair
per block, not 24 independent phenomena or a wording-robust benchmark.

Absolute choices expose an important unresolved issue: positive interactions can
coexist with persistent candidate preferences. Positivity, negation, length,
lexical wording, and context-dependent tokenization remain possible contributors.
Relabeling A/B together with eta was only bookkeeping and did not control these
effects. The absent condition leaves an empty message and therefore has its own
prompt artifact.

Within-context emoji token-position arrays differ in **24/48 emoji-pair
comparisons**. The baseline kept these pairs. Equal-position K/V exchange cannot
simply be applied to the whole population: the future protocol must define
eligibility without using observed effects and keep its excluded denominator.
Matching the remaining positions alone would still not establish semantic or
causal comparability.

| Required work | Current state |
| --- | --- |
| Independent human interpretation with ambiguous/both/neither options | Not performed; all labels remain author-defined |
| Additional fixed candidate phrasings | Not performed; J = 1 |
| Ordinary-word alternatives | Proposed in the stimulus records; not forwarded |
| Non-emoji symbol carriers and a matched legend design | Not finalized or forwarded |
| Natural-state bidirectional message exchange | Not instrumented or executed |
| New-family confirmation and a second model family | Not performed |

The next bounded development step should compare fixed ordinary-word controls
and several candidate phrasings across **all six families**, including the weak
and negative cases. The smallest first comparison is the existing word pairs
with the unchanged candidates: 24 blocks × two contexts × two words × two
candidates = 192 new scoring cells. Candidate paraphrases are a separate, later
allocation. Keep this version intact and specify each new allocation
before running it. Do not select only the strongest family as if it were an
untouched hypothesis. Independent stimulus validation and a calibrated causal
implementation follow; confirmation requires separately prepared new families.

## Acquisition and independent arithmetic check

The revised, 25-page working PDF was built and visually checked before the first
model forward. Its SHA-256 is
`43a5931dd5d3de578818298c8a92fbc9f9244c08d0a821d30fce63e1f4645898`.
The PDF describes the successor study as future work; **these pilot results have
not been inserted into the manuscript**. Historical submission artifacts remain
unchanged.

Acquisition source commit: `bb4200f1f764e2d2456269f9735f486ca0444f7e`.
The fixed stimulus SHA-256 is
`3222695420917983d79d84e55364dd07a86b61b29ecc4d6dfdadedccde72f394`.
Preparation, with zero model forwards, bound all 288 cells to their token IDs,
input/config/source files, tokenizer, runtime, and model artifact manifest.

The existing model revision was `60a99aaf43164077157d64bf909b7b61143c6a6d`, with
artifact-manifest SHA-256
`dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`,
matching the prior T21 artifact pin. No model was downloaded. A separate Furnace
checkout was used; other workloads and the existing research checkout were not
modified. GPU availability was checked immediately before each run.

Execution used RTX 5090, Python 3.14.4, Torch 2.13.0+cu132, Transformers 5.15.0,
and tokenizers 0.22.2, with BF16 eager attention and `use_cache=False`.
Full candidate log probabilities were summed without length normalization,
added BOS/special tokens, EOS scoring, or a chat template. Joint tokenization
passed the exact-prefix boundary check for every cell.

The separate smoke run completed 12/288 planned cells and retained the other
276 as `not_run`. It is deliberately partial, not a failed experiment or an
independent replication. The full run then completed 288/288, starting at
2026-10-06 18:29:06 UTC (2026-10-07 03:29:06 JST). Thus **300 acquisition
forwards** occurred across both runs; the scientific descriptive denominator
uses only the 288 full-run cells. The repeated 12 scores agreed exactly.
The full run recorded 7.90 seconds including model load and 3.33 seconds in its
scoring loop. These are run timings, not a backend speed comparison. A final
occupancy check found no GPU compute process.

An independent, standard-library-only validator reconstructs sequence sums from
every saved token log probability, then all block scores, interactions, family
means, and denominators. Only afterward does it compare the saved summary.
All 288 token sums and all 231 floating-point summary comparisons agreed exactly.
The smoke run retains null full-population estimates. This checks stored scalar
arithmetic and receipt consistency; it does not rerun the model or establish
scientific replication, human validity, or causal correctness.

All 76 targeted tests passed across the pilot runner, independent validator,
existing evidence checks, and figure-layout checks. Local scoring tests used a
tiny randomly initialized model, not a downloaded research model. Test success
checks implementation behavior; it does not expand the scientific claim.

Artifacts:

- [Separate preparation receipt](../validation/contextual_emoji_output_pilot_v0/specification.json)
- [Full raw scored cells](../validation/contextual_emoji_output_pilot_v0/full288/cells.jsonl)
- [Full summary](../validation/contextual_emoji_output_pilot_v0/full288/summary.json)
- [Independent validation with exploratory diagnostics](../validation/contextual_emoji_output_pilot_v0/full288/independent_validation_with_diagnostics.json)
- [Earlier arithmetic-only validation, preserved](../validation/contextual_emoji_output_pilot_v0/full288/independent_validation.json)
- [Partial smoke receipt](../validation/contextual_emoji_output_pilot_v0/smoke12/run_completed.json)

The preparation SHA-256 is
`04d7d005ee5c6555ef85cf900d79f79b88a50e7681001502ed3cd5be0d95bcd5`;
full scored cells SHA-256 is
`ce090b817ea5c0ebf5382d1b1994a482f918d06043821d94157c0b2710980d97`.
Acquisition records retain internal execution paths for provenance. A future
public package needs a separately described portable export; do not silently
rewrite these original receipts.

Run the non-model validation from the repository root:

```bash
python3 scripts/validate_contextual_emoji_output_pilot_v0.py \
  --specification validation/contextual_emoji_output_pilot_v0/specification.json \
  --run-dir validation/contextual_emoji_output_pilot_v0/full288 --require-full
```
