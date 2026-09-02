# T21: Glyph-position context path pilot

[日本語](T21_GLYPH_CONTEXT_PATH_PILOT_V0.ja.md) | [T20](T20_LEXICAL_ALIAS_OPTIMIZED_SUBSPACE_CAUSAL_V0.md)

## Purpose and current boundary

This exploratory pilot follows the T20 readout-state swap asymmetry. It uses
only the **384 already evaluated T20 items**, plus the **128 already used T19
source items** as donors and fixed distractors. The remaining **195 items are
not selected, tokenized, forwarded, or inspected** by this pilot. Its runner
contains no reserve-selection or confirmation command. The submission-ready
paper at commit `896b942` remains the reference submission version.

The pilot asks whether late attention messages from glyph positions contribute
to corresponding-keyword retrieval after the readout residual has been
replaced with the same item's codepoint-view state. The two candidate anchors
are blocks 21 and 24 of the same Llama 3.2 3B BF16 model used in T20.

## Intervention and controls

After each anchor, replace post-RoPE keys and values with those of a different
source emoji having the **same glyph token count**. Only the attention output
for the readout query can change. All other query outputs, readout self-key/value
messages, model weights, and the rest of the computation are preserved.
Two deterministic, distinct source donors are averaged for each target.

We compare glyph-position replacement with an equal-sized group of the nearest
preceding suffix positions. A broader control replaces every preceding-position
message; separate conditions restore either the own-item glyph messages or the
matched suffix messages. Intact-readout versions distinguish baseline dependence
from dependence following readout replacement. A donor-then-original round trip
must exactly reproduce the unmodified-reset result; that is an engineering check.

Both pipe and article carriers are read at distances 4 and 8. Distance 4 connects
to T20. **Progression decisions use distance 8**, where restoring glyph messages
and restoring the matched suffix span leave additional preceding positions
altered. At distance 4 for three-token glyphs, some contrasts are algebraically
identical; they are never counted as independent support.

## Measurement

The main continuous measure is own-keyword cosine similarity minus the maximum
similarity to the **same fixed 128 source keywords**. Each item therefore has one
correct keyword and 128 distractors, regardless of the evaluation-set size.
Own-versus-donor keyword margin, keyword top-1, and codepoint retrieval are also
reported. A gallery is always read under the same carrier and distance as the
query. Changing this measure does not change any historical T20 result or rule.

Within-item means average the two donors and, for progression, the two
distance-8 carriers. Bootstrap intervals resample target items, conditional on
the fixed source donor/gallery set; repeated contexts are not independent items.

## Pilot progression rule

All exact engineering checks and complete acquisition must pass. At either
candidate anchor, the lower 95% bootstrap bounds must be positive for:

1. The reset-versus-all-prefix-donor calibration contrast.
2. The absolute glyph-replacement decrement.
3. The decrement relative to equal-sized suffix replacement.
4. The glyph-restoration increment after all-prefix replacement.
5. The restoration increment relative to matched suffix restoration.

This is a **pilot screen**, not a corrected confirmatory test. If both anchors
pass, choose the larger minimum lower bound across contrasts 2–5, breaking ties
by lower anchor. A passing screen permits preparation of a separate prospective
protocol; it does not itself admit reserve-item execution. Effect-size meaning,
power, multiplicity, galleries, and stopping rules must be recorded before any
reserve item is accessed. A failed calibration leaves the pathway hypothesis
unresolved. A calibrated failure constrains this particular intervention and
endpoint, without excluding other paths.

## Execution and integrity

Config: [`t21_glyph_context_path_pilot_v0.yaml`](../configs/t21_glyph_context_path_pilot_v0.yaml).
Runner: [`t21_glyph_context_path_pilot_v0.py`](../scripts/t21_glyph_context_path_pilot_v0.py).

The specification binds source files, selection hashes, token sequences, donor
indices, and the previously measured model artifact. New outputs use exclusive
creation; completed chunks are immutable and hash-checked on resumption. An
eight-item engineering canary precedes the 384-item run. Foreign GPU contention
causes an immediate cooperative exit at the next item boundary. A 90-minute
per-invocation runtime budget prevents an unattended extension.

Transformers eager attention is used because the experiment requires internal
residual and query-specific key/value interventions that the managed generation
interface does not expose. Existing environments and system CUDA are unchanged.
No generation is performed. The existing paper and anonymous archive remain
unchanged until the new evidence has been checked separately.
