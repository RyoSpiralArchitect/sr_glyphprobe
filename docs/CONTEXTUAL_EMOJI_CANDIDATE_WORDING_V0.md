# Candidate-wording sensitivity on the same 24 scenarios

[日本語](CONTEXTUAL_EMOJI_CANDIDATE_WORDING_V0.ja.md)

The bounded acquisition is now complete; see the [separate results](CONTEXTUAL_EMOJI_CANDIDATE_WORDING_V0_RESULTS.md).
The design below preserves the choices made before the new scores were obtained.

Status: development design written before acquiring the additional candidate
scores, after observing the original emoji and word-control results. This is
not a new confirmatory bank or an isolated test of negation.

## Question and fixed design

Does the observed context-by-cue interaction persist when the two scored
continuations change? The previous emoji and word-control means were 1.312269
and 2.250543, respectively, with author-label alignment of 54/96 and 60/96.
Those results do not establish emoji-specific contextual interpretation.
Candidate wording is a measurement sensitivity worth resolving first.

Keep all 24 development blocks (six families, four blocks each), both original
contexts, both cue variants, and both emoji and word carriers. Keep the model,
BF16 arithmetic, eager attention, and unnormalized whole-continuation log
probability scoring. No generation, training, or intervention is planned.

Three continuation pairs are reported separately:

| Pair | Positive continuation | Negative continuation |
| --- | --- | --- |
| Original | Original scenario-specific text | Original scenario-specific text |
| Goal compatibility with explicit negation | ` This meets my goal.` | ` This does not meet my goal.` |
| Goal compatibility with adjectives | ` This is suitable for my goal.` | ` This is unsuitable for my goal.` |

Leading spaces are literal. The positive continuation occupies candidate A for
eta=+1 and candidate B for eta=-1, preserving the original orientation. The two
new pairs are global; they are not chosen by family or outcome. The 24 original
pairs remain unchanged. The panel is author-defined without human validation.
The labels are shorthand: both new pairs also change lexical content, token
length, specificity, and morphology. Their difference cannot identify a pure
negation effect, and the pairs are not asserted to be meaning-equivalent.

## Denominators and acquisition order

- 192 distinct crossed prompts across both carriers.
- 384 original crossed scores reused: 192 emoji and 192 word. The 96 original
  absent-cue scores are excluded from this comparison.
- 768 additional candidate scores: two new pairs × 24 blocks × two contexts ×
  two carriers × two variants × two continuations.
- 1,152 combined crossed scores, still only 24 development blocks.
- An additional 384 engineering forwards repeat the original crossed cells to
  check the changed weight placement. They are not independent observations.
- At most 1,152 new model-forward attempts (384 parity + 768 new candidates).
  Model loading and both stages share a 900-second soft wall-clock bound,
  checked between forwards. A running forward may finish beyond that bound.

The original-score parity stage precedes every new candidate score. New-score
order is pair, block, context, carrier, variant, candidate. No outcome-driven
reordering, best-pair selection, or implicit retry/resume is permitted. Every
planned cell is retained as completed, failed, failed-preflight, or not-run.
If a boundary or budget fails, full-panel aggregates are unavailable rather
than imputed from available rows. There are no new absent-cue forwards; old
absent-cue scores cannot be reused for different continuation strings.

## Bounded coexistence on Furnace

The user explicitly authorized assessing spare-VRAM coexistence with Aether.
Read-only observation on 2026-10-07 found 8,540 MiB free while Aether PID 485817
held 23,540 MiB. Utilization ranged from 24% to 100% in twelve observations;
spare VRAM is not spare compute. This historical observation is not a lease.

The full BF16 parameter storage is about 6,128 MiB. Instead, retain decoder
weights on CPU and transfer one decoder block at a time to CUDA. Embeddings,
tied output weights, final normalization, and rotary buffers stay on CUDA.
Layer hooks restore the immutable CPU storage after each block, also on errors.
This changes placement and transfer overhead, not quantization or the intended
arithmetic device. CUDA numerical equivalence remains an empirical gate.

The source-bound compute policy requires:

- PyTorch allocator cap 2,560 MiB plus a 512 MiB driver allowance.
- At least 7,168 MiB free before allocation and 4,096 MiB free during scoring.
- Only the previously observed peer PID 485817 may coexist; a new peer PID,
  unreadable state, insufficient memory, or own allocation above 3,072 MiB
  stops this acquisition. The peer may exit normally.
- Guards before and after each forward; a minimum 0.1 seconds between starts.
  Input length is bounded at 96 tokens, candidate length at 64, batch size one.
- Exact equality of every per-token log probability and sequence sum on all
  384 historical crossed cells before any new candidates. The first mismatch
  stops; no tolerance widening or automatic alternative placement.
- Release our staged weights on failure and completion. Do not alter, pause,
  reprioritize, inspect scientific outputs from, or kill the peer workload.

These checks neither reserve memory nor guarantee zero impact on Aether's
throughput. They cannot preempt a concurrent allocation race or a running
kernel. A failed trial is a valid outcome. Core runtime equality is recorded
separately from the changed placement and observed numerical parity.

## Analysis and claim limits

For each pair, define s(c,v)=log P(A|c,v)−log P(B|c,v),
delta_c=s(c,b)−s(c,a), and H=eta(delta_q−delta_p). Report H, the two deltas,
directional crossover, absolute author-label alignment, ties, and all-four
alignment. Positive H, effect crossover, and absolute alignment are different
outcomes. Report all family means, all negative results, and token geometry.
No geometry-based exclusions or claims of token matching are allowed.

For each block/carrier, report all three H values, their mean/range/sign
stability, crossover across all pairs, and label-preference stability. Report
word-minus-emoji H for each pair and its equal-pair mean. Aggregate only
complete sets with equal pair/family weights. There are no p-values, bootstrap
intervals, H ratios, or population generalization claims. These repeated
measurements cannot triple the number of independent scenarios.

Consistency would strengthen the robustness of a conditional-probability
measurement on this panel. Sensitivity would narrow its interpretation. Neither
outcome alone establishes emoji meaning disambiguation, a causal pathway,
free-generation behavior, or an advantage over words.

## Reproducible entry points

The source-bound config is `configs/contextual_emoji_candidate_wording_v0.json`;
the panel is `data/contextual_emoji_candidate_wording_v0.json`. Original inputs,
specifications, raw scores, and helper scripts have fixed SHA-256 identities.
Both protected historical target banks remain closed and unused.

```sh
python scripts/contextual_emoji_candidate_wording_v0.py plan \
  --config configs/contextual_emoji_candidate_wording_v0.json --output /NEW/design.json
python scripts/contextual_emoji_candidate_wording_v0.py prepare \
  --config configs/contextual_emoji_candidate_wording_v0.json \
  --model-path /EXISTING/MODEL --output /NEW/specification.json
python scripts/contextual_emoji_candidate_wording_v0.py audit --specification /NEW/specification.json
python scripts/contextual_emoji_candidate_wording_v0.py run \
  --specification /NEW/specification.json --output /NEW/run --acknowledge-development-only
python scripts/summarize_contextual_emoji_candidate_wording_v0.py \
  --run-dir /NEW/run --specification /NEW/specification.json --output /NEW/analysis.json
```

The plan command is text-only. Prepare uses the pinned existing remote runtime
and local tokenizer without forwards or downloads. Run requires another live
resource check. CPU synthetic tests validate arithmetic and stop/receipt
behavior; only a real CUDA trial can validate actual memory use and parity.

## Implementation correction before any forwards

The first attempt at source `b9e7ad2` stopped during core-runtime comparison:
0 parity and 0 new-candidate forwards. All 384+768 cells are retained as not-run
under `validation/contextual_emoji_candidate_wording_v0/shared_trial/`.
The comparison incorrectly used the live Python dictionary against parsed JSON;
Transformers' integer `id2label` keys become strings when saved. The correction
compares complete JSON representations, retaining every field and value. Tests
reject changes to every top-level runtime field and nested label values.
This explicit, separately recorded setup correction changes no stimuli, score
rules, memory limits, numerical tolerance, or forward budget. A new source-bound
specification and output directory are required for the next bounded attempt.
