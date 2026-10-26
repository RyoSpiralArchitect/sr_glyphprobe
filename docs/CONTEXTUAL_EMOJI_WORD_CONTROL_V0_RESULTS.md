# Ordinary-word control: development results

[日本語](CONTEXTUAL_EMOJI_WORD_CONTROL_V0_RESULTS.ja.md) | [Pre-acquisition protocol](CONTEXTUAL_EMOJI_WORD_CONTROL_V0.md) | [Emoji baseline](CONTEXTUAL_EMOJI_OUTPUT_PILOT_V0_RESULTS.md)

**Public-integration note, October 26, 2026:** this dated note retains the original
study status. References to excluded handoffs, notebooks, specifications or
runtime records concern the author's local archive; the public checkout does
not supply a complete historical run. See the
[public integration scope](PUBLIC_INTEGRATION_SCOPE_20261026.md).

Status, 2026-10-07: **192/192 word-control cells completed; the broader causal
study remains incomplete.** No public deposit, GitHub push, model download,
generation, training, or internal activation intervention occurred.

## Main observation

Replacing the emoji with the previously recorded word alternatives increased
the mean context-by-carrier interaction from **1.3123 to 2.2505 nats** on these
24 scenarios. Absolute agreement with the author's proposed candidate labels
increased from **54/96 to 60/96 inputs**. All-four-condition agreement appeared
in **3/24 blocks**, versus none for the emoji inputs.

Thus the measured interaction also occurs with ordinary words. Its magnitude
and absolute candidate preference remain distinct. The contrast helps diagnose
this output measurement; it does not identify an emoji-specific mechanism,
establish human agreement, or demonstrate free-generation accuracy.

## Complete, paired results

Both conditions use the same 24 blocks, two contexts, two candidate strings,
and orientation labels, with the same pinned Llama 3.2 3B base BF16 model and
runtime. Only the source cue in the literal slot changes. The original words
were recorded before the emoji acquisition; the decision to run this follow-up
was made after seeing that acquisition. All six families remain included.

| Diagnostic | Existing emoji | New word control |
| --- | ---: | ---: |
| Mean H, equal family weights (nats) | 1.3122693 | 2.2505428 |
| H positive | 23/24 | 23/24 |
| Intended sign crossover of the replacement effect | 12/24 | 18/24 |
| Higher-likelihood candidate agrees with proposed author label | 54/96 | 60/96 |
| Tied candidate scores | 0/96 | 0/96 |
| All four candidate preferences agree within a block | 0/24 | 3/24 |

The paired mean `H_word − H_emoji` is **+0.9382735 nats**. Word H is greater in
18/24 blocks and smaller in 6/24; there are no ties. These are finite-inventory
descriptions, with no p-values, population confidence intervals, or calibrated
practical-effect threshold. No ratios of H are used.

The 96 corresponding inputs split into 48 aligned in both conditions, 12 aligned
only with words, six aligned only with emoji, and 30 aligned in neither. The
net improvement is six inputs, not uniformly better performance. The three
all-four-aligned word blocks are `thermal_02`, `completion_02`, and `affect_02`.
The only negative word H is `sound_01`, **−0.3098767**; it is retained.

| Family (four blocks each) | Mean H emoji | Mean H word | Word minus emoji | Proposed-label agreement emoji → word (/16) | Effect crossover emoji → word (/4) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Thermal goal | 0.885255 | 3.025010 | +2.139755 | 9 → 11 | 3 → 4 |
| Sound goal | 0.822570 | 1.857611 | +1.035041 | 8 → 8 | 3 → 3 |
| Completion goal | 1.574031 | 1.712608 | +0.138576 | 9 → 10 | 0 → 3 |
| Affect-tone goal | 2.477807 | 1.904987 | −0.572820 | 11 → 11 | 4 → 3 |
| Direction goal | 0.218898 | 0.624440 | +0.405541 | 9 → 8 | 1 → 2 |
| Weather goal | 1.895054 | 4.378602 | +2.483547 | 8 → 12 | 1 → 3 |

The affect family has the opposite mean-H contrast to the other five families.
The direction family's H rises while its absolute agreement falls. Both remain
visible; neither licenses selecting a favorable family as a fresh hypothesis.
With the balanced author orientation, the mean change in author-oriented
candidate margin equals `mean(D_H)/4` algebraically. It is not independent
support for the H comparison.

## Important unmatched dimensions

**This is a lexicalization comparison, not a meaning- or token-matched test.**
Words can make a status explicit, repeat goal vocabulary, or remove ambiguity
present in an icon. Their advantage cannot isolate representational quality.

Carrier token-position arrays and prompt token counts differ between words and
emoji in **84/96 corresponding inputs**. Within the word condition, word A/B
positions and prompt counts differ in **12/48 context pairs**. All cases were
retained; no matched subgroup was selected after outcomes. All corresponding
candidate token sequences agree, and all exact joint-prefix checks passed.

Each block still has only one candidate pair. Candidate wording, negation,
preference, context-dependent tokenization, and unvalidated scenario assumptions
remain alternatives. All labels remain author-defined. Higher H and effect
crossover do not require the most probable candidate to reverse. The saved
emoji-absent scores are reused diagnostics with an empty-message artifact, not
new or independently replicated controls.

## Acquisition and verification

Acquisition code/config/protocol commit:
`18b924699212946fd508cc1e7a31413f2a26101a`.
The fixed allocation was 24 × two contexts × two words × two candidates:
**192 new sequence forwards, 96 inputs, 24 complete blocks, zero failed or
missing cells**. No smoke rerun or extra emoji/absent forwards were added.
The original emoji comparator is its full 288-cell run, not the earlier smoke.

The run began at **2026-10-06 18:56:45 UTC / 2026-10-07 03:56:45 JST** and took
10.95 seconds including model loading; the acquisition loop took 6.30 seconds
including per-cell occupancy checks and durable writes. This is a run timing,
not a speed benchmark. Each forward was preceded by a check for other GPU
compute PIDs. No competition was detected; a post-run status check found no GPU
compute process. No other workload was modified.

Model loading was local-only. The artifact manifest matched the prior model,
and **the full runtime JSON is byte-identical to the emoji baseline**, including
Python/package versions, CUDA/backend, model and attention implementation hashes,
device, and scoring-related settings. No BOS/special tokens, EOS, chat template,
length normalization, or KV cache were added.

| Artifact | SHA-256 |
| --- | --- |
| New preparation specification | `ba8eabb588d48eca68041f475440e64b3f6e0db1fa6ab4f5aa56ee7083b0c519` |
| New raw scored cells | `1026d3001ad4390662bfec608cfeca28d1610f7ba7117b6401494d8fa929ad91` |
| Runtime, identical in both runs | `952139aec861ada4b9c889b36933a0f65c520c393d61d80e308f81b3df41e323` |
| Independent comparison | `830ba534f5c9c44b640598c0e869b3c7bb3ec16e98d3ed85e52c08d38e0a9495` |

The standard-library-only independent comparison reconstructs scores from the
saved token probabilities, checks source cue/candidate identity and receipt
hashes, then compares the saved aggregates. It also reconstructs both carriers'
family means, absolute preferences, paired transitions, and token geometry.
It does not import either runner, load a model/tokenizer, or conduct statistical
inference. This is a check of saved arithmetic and provenance consistency,
not independent model replication or validation of the author labels.

Targeted tests passed: **109 tests and 17 subtests**, covering the new runner,
comparison, previous pilot/validator, and existing paper/evidence checks.
Historical stimuli, baseline records, and the revised PDF were not changed.
Raw receipts retain internal execution paths; a public release needs a separate
portable export and rights review. Publication remains deferred.

Artifacts on this Mac:

- [Preparation](../validation/contextual_emoji_word_control_v0/specification.json)
- [Raw scored cells](../validation/contextual_emoji_word_control_v0/full192/cells.jsonl)
- [Independent comparison](../validation/contextual_emoji_word_control_v0/full192/independent_comparison.json)
- [Occupancy checks](../validation/contextual_emoji_word_control_v0/full192/occupancy_checks.json)

The original machine-specific records remain in the author's local archive.
The October 26 public integration includes the scored cells, comparison and
summary unchanged, but excludes the execution specification and occupancy
records. This is partial historical evidence, not a complete portable run.
See the [public integration scope](PUBLIC_INTEGRATION_SCOPE_20261026.md).

With the omitted original specification available in the local archive,
recompute the model-free comparison into a **new** output path:

```bash
python3 scripts/compare_contextual_emoji_word_control_v0.py \
  --word-specification validation/contextual_emoji_word_control_v0/specification.json \
  --word-run-dir validation/contextual_emoji_word_control_v0/full192 \
  --emoji-run-dir validation/contextual_emoji_output_pilot_v0/full288 \
  --output /tmp/glyphprobe-word-comparison-new.json
```

## Next discriminating step

The current result suggests checking the stability of the **measurement** before
localizing an internal mediator. Specify several alternative candidate phrasings
for all 24 scenarios, retaining both emoji and word conditions and all six
families. Keep this J = 1 version intact and report sensitivity rather than
choosing a favorable wording. Independent human interpretation validation is
still needed, followed by separately specified natural-state causal controls
and new-family confirmation. These steps were not executed in this run.

Follow-up: the [same24 candidate-wording study](CONTEXTUAL_EMOJI_CANDIDATE_WORDING_V0_RESULTS.md)
subsequently completed 768 additional scores. Its records and conclusions are
separate from this unchanged J = 1 acquisition.
