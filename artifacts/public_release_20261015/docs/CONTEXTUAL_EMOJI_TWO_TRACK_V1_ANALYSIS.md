# Two-track development: analysis boundary

[日本語](CONTEXTUAL_EMOJI_TWO_TRACK_V1_ANALYSIS.ja.md) · [Design](CONTEXTUAL_EMOJI_TWO_TRACK_V1.md)

## Private author-response analysis

The analysis is separate from the already bound v1 interface and acquisition.
Do not edit that interface, its protocol documents, the v0 records, or the
original response journal to accommodate later interpretations.

1. `scripts/analyze_contextual_emoji_two_track_author_v1.py describe` validates
   the finalized journal through a read-only descriptor. It checks package and
   interface hashes, request identities, state replay, timestamps, and complete
   denominators without opening the assignment key or model results.
2. Write English/Japanese `PHASE_ONE` notes in the private analysis directory,
   then run `seal`. The timestamped digest records that interpretation before
   current assignment/model exposure; it does not erase earlier knowledge or
   constitute preregistration.
3. Record `comparison_exposure.json` bound to the seal before reading the key.
   `scripts/compare_contextual_emoji_two_track_author_v1.py` verifies that binding,
   repeats the independent numerical audit, recomputes all candidate scores,
   and joins each human question by its exact scene and question text.
4. `scripts/diagnose_contextual_emoji_two_track_readout_v1.py` decomposes the
   saved sequence score into the divergent answer token and following period.
   This is a post-result diagnostic, not a replacement primary estimator.
5. `scripts/build_contextual_emoji_two_track_author_notebook_v1.py` creates the
   private executable companion. Run it top-to-bottom with nbformat, nbclient,
   and ipykernel; it replays the journal and recomputes the saved analyses.

Each stage refuses to overwrite its output. Actual participant packets,
assignments, raw responses, interpretation notes, and human-linked analyses
remain on the local Mac outside Git and SpiralShare. Do not put them in the
furnace checkout. The repository contains only generic analysis code, synthetic
tests, and this methodological guide. Keep source hashes beside the private
artifacts. A later analysis change needs a new output version rather than an
edited receipt.

## Denominators and interpretation

The packet has 24 scenes and 36 substantive judgments: 12 local matches and 12
naturalistic scenes with two questions each. They are not 36 independent
scenarios. Undecidable, explicit abstention, and missingness are distinct;
undecidable is never recoded to No. Optional missing metadata is not a favorable
quality judgment. Keep known author exposure separately from self-report.

Human/model agreement uses only binary human judgments and non-tied model
scores. This response-selected subset is not human-gold accuracy. Primary joins
use the same positive question; normalized negative wording is a sensitivity
analysis the participant did not answer. Authored local-match references and
logical anchors are not independent human labels.

The full model readout retains all carriers, families, propositions, polarities,
absent cues, and explicit complete/unknown anchors. A true/false wording pair
should reverse the literal answer to preserve the underlying proposition. The
two wordings are repeated views, not additional scenario N. Context-by-cue
contrasts are descriptive sequence-likelihood interactions, not causal
effects or established emoji superiority. The primary estimator is the original
full answer-sequence log probability; token-only diagnostics must retain ties.

Keep numerical integrity and semantic suitability separate. A perfectly
reproduced acquisition can fail explicit evidence or polarity controls. Such a
failure limits interpretation of this model/prompt/readout configuration; it
does not establish a general inability of the model or invalidate unrelated
experiments. An author pilot can motivate a smaller instrument-qualification
study, but cannot replace independent raters and newly prepared scenario
families. This analysis does not launch new compute, update manuscript numbers,
recruit participants, push Git, or publish private data.
