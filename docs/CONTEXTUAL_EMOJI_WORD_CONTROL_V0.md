# Ordinary-word control: development protocol

[日本語](CONTEXTUAL_EMOJI_WORD_CONTROL_V0.ja.md) | [Emoji baseline](CONTEXTUAL_EMOJI_OUTPUT_PILOT_V0_RESULTS.md) | [Separate acquisition results](CONTEXTUAL_EMOJI_WORD_CONTROL_V0_RESULTS.md)

Protocol: `glyphprobe-contextual-emoji-word-control-v0`.
Specified on 2026-10-07 before any word-control model forward. The emoji results
were already known, and this follow-up was selected afterward. It is development
work, not a preregistered or untouched confirmation. No publication is performed.

## Question and exact allocation

How does replacing emoji with the **already recorded ordinary words** change the
context-dependent relative likelihood of the same candidate continuations?

Use all 24 original scenario records, with their six families and four blocks per
family. Replace only the literal `{emoji}` slot with the corresponding existing
`planned_word_alternatives.a` or `.b`. Contexts, candidate strings including
whitespace and punctuation, eta, and author orientation maps stay unchanged.
No new prompt instruction or word legend is added. No block or wording is
revised after seeing the emoji results.

The allocation is **24 blocks × two contexts × two words × two candidates =
192 new candidate-sequence cells**, representing 96 inputs. There are no new
emoji or absent-control forwards. Previous full-run emoji and absent scores are
comparators; the 12-cell smoke run is excluded. No result is pooled as a replicate.

An independent read-only audit before word acquisition checked all 24 stored
word pairs and their orientation. It found no execution-blocking wording issue
and recommended preserving all pairs. This is an agent design review, not
independent human interpretation validation.

## What this control does and does not match

| Family | Existing word alternatives across its four blocks | Remaining ambiguity |
| --- | --- | --- |
| Thermal | hot/cold; hot/cold; warm/cool; warm/cold | Text makes temperature explicit; fire can communicate intensity, quality, or danger. |
| Sound | sound on/muted; sound on/muted; audio enabled/audio muted; unmuted/muted | State, interface action, and notification versus media sound are not equivalent. |
| Completion | finished/pending; shipped/awaiting shipment; complete/pending; confirmed/awaiting confirmation | An unfinished or unconfirmed state does not guarantee that editing or cancellation is permitted. |
| Affect | smiling/crying; a smiling face/a crying face; a smile/tears; smiling/crying | Expression descriptions do not uniquely determine emotion or suitability for a scene. |
| Direction | up/down; upward/downward; up/down; upward/downward | Direction alone does not establish destination, displacement, or execution. |
| Weather | sunny/rainy; sunshine/rainfall; sunny/rainy; sunny/rainy | Duration and intensity remain unspecified. |

This is a **lexicalization control**, not a token-matched or independently
meaning-matched control. Word phrases often repeat goal vocabulary and state
the intended interpretation more explicitly. A word/emoji difference can reflect
this explicitness, lexical overlap, ambiguity, tokenization, or the single
candidate pair. It does not by itself establish emoji specificity or a mechanism.

## Fixed descriptive comparison

For both carriers, reconstruct full continuation log-probability sums and compute:

```text
s(c,x)  = log P(candidate_a | c,x) - log P(candidate_b | c,x)
Delta_p = s(p,b) - s(p,a)
Delta_q = s(q,b) - s(q,a)
H       = eta * (Delta_q - Delta_p)
D_H     = H_word - H_emoji
```

Retain all four scores, both deltas, H, and `eta * Delta_p < 0 < eta * Delta_q`
as an effect-crossover diagnostic. Report H-positive counts and paired delta
differences. Compute six family means and their equally weighted mean, retaining
the 24-block denominator and failed/missing cells. An incomplete planned family
or population does not receive a full-family or full-population estimate.

Separately report the higher-likelihood candidate agreeing with the author's
proposed label over **96 crossed inputs**, ties, and agreement in all four inputs
over **24 blocks**. Report paired outcomes (both aligned, emoji only, word only,
neither); retain ties explicitly. These measure proposed-label preference, not
human-validated accuracy or free-generation performance. Positive H and an effect
crossover need not change the preferred candidate.

Keep prompt and carrier-span token counts/positions, candidate token sequences,
the exact joint-prefix boundary, and the first prediction position. Report
within-word geometry over 48 context pairs and corresponding emoji/word geometry
over 96 input pairs. No post-outcome token-matched subset replaces the full result.
Previously recorded absent-input scores remain a diagnostic with an empty-message
artifact, not an additional acquisition or independently replicated control.

No p-values, bootstrap, population intervals, H ratios, or post-hoc success
thresholds are specified. All positive, zero, negative, and uncertain cases stay.

## Execution and reproducibility limits

The [configuration](../configs/contextual_emoji_word_control_v0.json) pins:

- Original stimulus SHA-256: `3222695420917983d79d84e55364dd07a86b61b29ecc4d6dfdadedccde72f394`.
- Baseline preparation SHA-256: `04d7d005ee5c6555ef85cf900d79f79b88a50e7681001502ed3cd5be0d95bcd5`.
- Full baseline raw-cell SHA-256: `ce090b817ea5c0ebf5382d1b1994a482f918d06043821d94157c0b2710980d97`.
- Baseline runtime record SHA-256: `952139aec861ada4b9c889b36933a0f65c520c393d61d80e308f81b3df41e323`.
- The same Llama 3.2 3B base BF16 artifact manifest: `dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`.

Use the existing model, the baseline Python/package versions, eager attention,
and no KV cache. Preserve the prior scoring convention: full candidate token
log-probability sum, no length normalization, added special/BOS tokens, EOS,
or chat template. A failed exact-prefix check is a failed cell, not a fallback.
Before the first forward, compare model/attention implementation hashes and
runtime identity fields to the pinned baseline runtime record as well.

Preparation binds source, input, config, tokenizer, model, runtime, and all 192
cells without a model forward. Run only after source tests, an idle Furnace
check immediately before compute, and a validated preparation receipt. Use an
isolated checkout and new result directory. Stop the current acquisition if a
competing GPU workload is detected; never stop or change another workload.

Maximum new forwards: 192; full input limit: 512 tokens; candidate limit: 64
tokens within that total; acquisition bound: 900 seconds. Preserve all planned
records on a failure or interruption, and do not silently rerun them. No download,
dependency installation, free generation, training, causal intervention, or
protected historical target-bank access is part of this run.

An independent model-free comparison reconstructs scores from stored per-token
values and checks input identity, counts, model/runtime parity, and file hashes.
This validates recorded arithmetic and provenance consistency, not the human
labels, the model's internal computation, or independent scientific replication.

## How the result informs the next step

If words also move H while leaving absolute candidate agreement weak, generic
goal-compatibility processing and candidate wording remain important suspects.
If words improve proposed-label preference, the response metric has useful
headroom, and emoji ambiguity or weaker conditioning deserves closer inspection.
Either pattern remains development evidence. Candidate paraphrases, independent
human validation, non-emoji carriers, and calibrated natural-state interventions
are later allocations, not results of these 192 cells.
