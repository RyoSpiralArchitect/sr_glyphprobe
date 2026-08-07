# E2 Llama 3.2 3B MPS emoji-transport v1 preflight failure

[日本語](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.ja.md) · [Frozen v1 protocol](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1.md) · [Machine-readable receipt](../validation/llama32_3b_mps_emoji_transport_v1/preflight_failure_receipt.json)

## Status

E2 MPS transport v1 stopped at its zero-model-forward tokenizer preflight. No
language-model weights were loaded, no model forward occurred, no launcher or
run namespace was created, and no scientific outcome exists. V1 is retired
before execution and must not be repaired or resumed in place.

The static freeze commit was
`a6803c7b673404b2bae4200cebe802b79cbc5782`. Its preflight failed with:

```text
Emoji token offset crosses wrapper text for w01_mark_anchor/sky_slot_00
```

## Cause

The raw glyph in the triggering profile has token IDs `[9468, 234, 239]`.
Inside that source wrapper, the immediately preceding space and the first emoji
component form contextual token `11410`, giving `[11410, 234, 239]`. The first
token's offset is `(5, 7)` while the emoji occupies character interval `(6, 7)`.
The frozen v1 audit incorrectly required every overlapping contextual token to
have the raw-glyph offset and raw-glyph ID.

This is a preflight-specification failure, not a model result. A tokenizer-only
diagnostic over the complete public wrapper/panel surface found two exact
contextual first-token profiles: `9468` in seven wrappers and `11410` in nine.
For all 16 wrappers, the 35-item core arm still had a constant three-token span,
the expected family-middle and matched-slot suffix structure, constant positions
and counts within wrapper, and an invariant outside-token sequence. These facts
motivate a new audit; they do not retroactively pass v1.

## Disposition

A v2 study must use a new protocol ID, manifest, configurations, preflight
receipt, run names, validation receipts, analysis destination, and publication
bundle. Its preflight must separately freeze:

- exact raw-glyph token IDs;
- exact per-wrapper contextual first-token and offset profiles;
- the contextual core pattern `[wrapper_first, family_middle, slot_suffix]`;
- constant positions, counts, anchors, and outside-token sequences within each
  wrapper.

The scientific panel, model, layers, strength, targets, wrappers, bootstrap,
primary endpoint, and claim boundary may remain unchanged only if they are
bound anew before any model forward. V1 contributes no evidence for or against
emoji transport.
