# Candidate wording: positive interactions, sensitive candidate preferences

[日本語](CONTEXTUAL_EMOJI_CANDIDATE_WORDING_V0_RESULTS.ja.md) ·
[Design](CONTEXTUAL_EMOJI_CANDIDATE_WORDING_V0.md)

**All 768 additional candidate scores completed, with no missing cells.** On
the same 24 development scenarios in Llama 3.2 3B, mean emoji interaction H was
positive for all three continuation pairs (1.196–1.316). The higher-scoring
candidate's author-defined polarity changed across pairs on 52/96 emoji inputs
and 56/96 word inputs. A positive interaction and a stable absolute candidate
preference are therefore distinct properties of this measurement.

This is teacher-forced sequence scoring, without generation. The new phrases
were specified after seeing the original results. They change length,
specificity, vocabulary, and morphology together and have no human equivalence
validation. These data do not isolate negation, establish emoji-specific meaning
disambiguation, or support a causal claim.

## Complete results

H=eta(delta_q−delta_p), with delta_c=s(c,b)−s(c,a) and
s(c,v)=log P(A|c,v)−log P(B|c,v). H and its averages are in natural-log units.
"Alignment" means agreement with the author's proposed labels, not validated
accuracy. Crossover requires eta·delta_p < 0 < eta·delta_q. No ties occurred.

| Candidate pair | Carrier | Mean H | H > 0 /24 | Crossover /24 | Alignment /96 | All four aligned /24 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Original, scenario-specific | Emoji | 1.312269 | 23 | 12 | 54 | 0 |
| Original, scenario-specific | Word | 2.250543 | 23 | 18 | 60 | 3 |
| Meets / does not meet my goal | Emoji | 1.196000 | 19 | 10 | 54 | 2 |
| Meets / does not meet my goal | Word | 1.611995 | 22 | 18 | 62 | 4 |
| Suitable / unsuitable for my goal | Emoji | 1.316048 | 24 | 14 | 55 | 2 |
| Suitable / unsuitable for my goal | Word | 2.311856 | 24 | 19 | 60 | 5 |

Across all three pairs, H stayed strictly positive in **19/24 emoji** and
**22/24 word** blocks. Crossover held in every pair in 6/24 and 13/24 blocks,
respectively. No block had negative H in every pair. Average within-block H
range was 0.797029 for emoji and 1.167160 for words (maxima 1.716005 and 3.117910).

The equal-pair means were 1.274772 (emoji) and 2.058131 (word). Word-minus-emoji
mean H was positive for each pair: 0.938273, 0.415995, and 0.995808. At block
level, this difference stayed positive in 14/24 blocks, negative in 4/24, and
changed sign in 6/24. The four consistently larger emoji interactions were
`completion_02`, `affect_01`, `affect_02`, and `affect_03`; they are descriptive
heterogeneity, not independently selected causal candidates.

Family means below preserve every planned family. Each entry is **emoji / word**.

| Family (four scenarios each) | Original | Meets / does not meet | Suitable / unsuitable |
| --- | ---: | ---: | ---: |
| Thermal | 0.885255 / 3.025010 | 0.648929 / 1.993614 | 0.991417 / 2.570652 |
| Sound | 0.822570 / 1.857611 | 0.719655 / 1.093043 | 0.526745 / 1.989208 |
| Completion | 1.574031 / 1.712608 | 2.048318 / 2.157335 | 1.930720 / 2.159475 |
| Affect | 2.477807 / 1.904987 | 2.136213 / 1.469520 | 2.288081 / 1.878178 |
| Direction | 0.218898 / 0.624440 | 0.291727 / 0.269087 | 0.402013 / 0.909082 |
| Weather | 1.895054 / 4.378602 | 1.331157 / 2.689373 | 1.757311 / 4.364539 |

All negative H values remain in the record: original emoji `direction_02`
(−0.222623), original word `sound_01` (−0.309877); explicit-negation emoji
`thermal_01` (−0.016952), `sound_01` (−0.011982), `direction_01` (−0.292182),
`direction_02` (−0.270887), `weather_02` (−0.125323); explicit-negation word
`sound_01` (−0.710076), `direction_01` (−0.054867). The adjective pair had no
negative H values. There were no zero H values or outcome-based exclusions.

## Interpretation and remaining controls

The panel-level interaction persists across the tested candidate changes.
Absolute label agreement remains limited and item-level preferences change
frequently, even when the aggregate agreement count looks similar. This result
supports reporting interaction magnitude, crossover, and absolute preference
separately. Words produce larger mean interactions in each pair, with clear
family and item heterogeneity. The data establish no general emoji advantage.

The two new pairs have unequal candidate lengths (5 vs 7 and 7 vs 8 tokens).
Full input lengths are 27–45 tokens. No length normalization or token-matching
claim is introduced. Global continuation wording and scenario-specific wording
also differ in specificity. New absent-cue conditions were not measured; old
absent-cue scores cannot substitute for new continuation strings. The combined
1,152 scored cells are repeated measurements on **24 development scenarios**;
shared families and cues also limit independence. No 72-scenario independent
sample, inferential p-values, or confidence intervals are claimed.

Before turning this into a semantic or causal claim, the next design needs
independent interpretation/equivalence validation and response controls that
separate wording and token-length effects, followed by unused-scenario testing.
No additional acquisition is authorized by this result alone.

## Spare-VRAM trial and exact historical parity

Acquisition source: `610fc77f3a371f8b983e43db179ba1718ef0cd61`. The isolated
Furnace checkout used existing model files and the historical BF16 CUDA runtime.
No downloads, quantization, model training, or changes to Aether were performed.
The run lasted **710.54 seconds** including loading, from
2026-10-07 04:41:14 to 04:53:05 UTC (13:41:14–13:53:05 JST).

CPU weight storage with one decoder block transferred at a time completed
**384/384 exact historical parity checks** before **768/768 new forwards**:
1,152 total forward attempts. Every historical per-token log probability and
sequence sum matched exactly, without widening the tolerance. The core runtime
JSON is byte-identical to the previous acquisition; changed weight placement
is disclosed separately. This is an engineering replication on historical
cells, not fresh scientific confirmation.

- Maximum observed own GPU-process memory: **1,666 MiB** (about 1.63 GiB).
- Peak PyTorch allocation: **979.38 MiB**; peak reserved memory: **990 MiB**.
- Minimum observed free VRAM: **6,868 MiB**, above the 4,096 MiB floor.
- **2,306** resource observations; **59** observed both our allocation and
  Aether PID 485817, from 04:41:19.360548 to 04:41:35.848783 UTC.
- Aether's GPU allocation then disappeared from observations; most of this run
  did not overlap it. This does **not** validate sustained coexistence or show
  that Aether training throughput was unchanged. Its scientific outputs were
  not inspected and completion of its training was not established.
- Our staged weights were released at completion. A subsequent GPU-process
  query returned no compute process. There was no memory-policy relaxation.

This is a successful bounded low-memory trial, not a speed benchmark. The
earlier setup-only stop at `b9e7ad2` is retained separately with zero forwards;
the JSON-key correction is described in the design document.

## Evidence and reproducibility

Local evidence directory:
`validation/contextual_emoji_candidate_wording_v0/runtime_fix/shared_trial/`.

| Artifact | SHA-256 |
| --- | --- |
| Prepared specification | `11a3c8112f69a9a2f69f542d79977e39f7fd49e5164f1def8600892d1ee1185e` |
| New scored cells | `ceeb391072ddfd42db7e464e5dbb715217dadeb90661516c6f1c2e326c872630` |
| Historical parity cells | `d9fab28226bf4d84d40983ce6698d940643e373ec9748c954adf3b81ef6e6a98` |
| Core runtime | `952139aec861ada4b9c889b36933a0f65c520c393d61d80e308f81b3df41e323` |
| Independent analysis | `1512f4ad613a4d9d20473c1a33af326412299c3a7f3a0d031551716ca753c719` |

The independent analyzer loads neither a model nor tokenizer. It checks raw
hashes, planned denominators, original stimuli and candidate identity, parity
values, resource-policy receipts, and per-token sums before computing the
reported statistics. This validates saved arithmetic/provenance, not human
labels or an independent reexecution of the new probabilities. Targeted tests:
**108 passed, 17 subtests passed**, including CPU-only failure/cleanup simulation.

```sh
python3 scripts/summarize_contextual_emoji_candidate_wording_v0.py \
  --run-dir validation/contextual_emoji_candidate_wording_v0/runtime_fix/shared_trial \
  --specification validation/contextual_emoji_candidate_wording_v0/runtime_fix/specification.json \
  --output /NEW/wording-analysis.json
```

The machine-specific originals remain in the author's local archive.
Historical raw data, protected target banks, and the revised PDF were left
unchanged by that acquisition. No publication or push occurred at that step.
The October 26 public integration retains scored cells, parity records and
analyses unchanged, but omits machine-specific specifications and runtime
receipts. The command above requires the omitted local specification; these
partial records are not a complete portable run. See the
[public integration scope](PUBLIC_INTEGRATION_SCOPE_20261026.md).
