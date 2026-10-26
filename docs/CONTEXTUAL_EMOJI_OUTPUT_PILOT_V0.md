# Contextual emoji output pilot: development protocol

[日本語](CONTEXTUAL_EMOJI_OUTPUT_PILOT_V0.ja.md) | [Successor-study plan](CONTEXTUAL_EMOJI_CAUSAL_TRANSFER_PLAN_V0.md) | [Separate development results](CONTEXTUAL_EMOJI_OUTPUT_PILOT_V0_RESULTS.md)

Protocol: `glyphprobe-contextual-emoji-output-pilot-v0`.
Status: **author-defined development design; no human validation; no result
reported here**. This protocol describes the first bounded output-scoring
pilot, not the proposed causal study or a confirmation experiment. Publishing
a completed study requires a separate evidence and release decision; building
this pilot does not complete that study.

## Purpose and scope

Ask whether replacing an emoji changes the ordinary base language model's
relative probability for two fixed natural-language assessments, and whether
that replacement effect differs between two contexts. The contexts reverse a
stated goal. Most blocks test compatibility between that goal and a plausible
emoji status cue. They do **not** require that the emoji itself changes meaning:
a stable cue and a context-sensitive response process can produce the predicted
interaction.

The [24 stimulus blocks](../data/contextual_emoji_development_v0.jsonl) were
authored for this development pilot, in English, without consulting CLDR
labels, historical target banks, or model outcome preferences. New sentences
are not a new-emoji or pretraining holdout. No claim is made that these scenarios
represent natural emoji use or the human population.

| Family | Four scenario settings | Emoji pair | Important unresolved reading |
| --- | --- | --- | --- |
| Thermal goal | drink, soup, room, towel | 🔥 / 🧊 | Fire can mean intensity, quality, or danger, not just warmth. |
| Sound goal | speaker, phone, exhibit, video | 🔊 / 🔇 | A control may display its action rather than current state; notification and media settings can differ. |
| Completion goal | printing, shipping, export, booking | ✅ / ⏳ | A check mark can mean acceptance rather than completion; pending status need not permit revision or cancellation. |
| Affect-tone goal | acting, drawing, storyboard, puppet | 😊 / 😢 | Smiles can mask sadness and tears can express joy; no binary human gold is supplied. |
| Direction goal | lift, camera, shelf, platform | ⬆️ / ⬇️ | Direction does not guarantee the destination, amount, or safe execution of a movement. |
| Weather goal | washing/barrel, filming, device test, fence/garden | ☀️ / 🌧️ | Suitability depends on duration and other conditions absent from these short prompts. |

All 24 blocks have `design_status: author_defined_development` and
`interpretation_status: unvalidated_author_defined`. Each carries its own
`uncertainty_note`. There are six families, not 24 independently validated
semantic phenomena. Emoji and templates repeat within families. The natural
behavioral evidence, if acquired, is therefore limited to this finite inventory.

## Crossed inputs and candidates

Each block stores `context_p` and `context_q`, each with one literal `{emoji}`
slot; `emoji_a` and `emoji_b`; and the same `candidate_a` and `candidate_b` for
all inputs. Rendering the slot with either emoji yields four crossed prompts.
Rendering it as an empty string yields two emoji-absent prompts. No artificial
blank marker is substituted, although the resulting message is visibly empty.
That empty-message artifact limits the absent control.

For example, one context requests a warming drink, the other a cooling drink;
the cafe's message contains either fire or ice. The continuations are the same
positive and negative assessments in all four cells. These are proposed
interpretations, not a claim that a person or model has endorsed them.

Prompts end with a plain narrative completion such as `Mira's assessment:`.
They do not list A/B options, issue a chat instruction, insert a system role,
or use a chat template. Candidate strings include their literal leading space
and terminal punctuation. This is teacher-forced scoring, not free generation.

For scoring-label bookkeeping, positive assessment is A in blocks 1/3 and B in
blocks 2/4 of each family. Each block records its intended mapping in
`orientation` and a sign `eta` (+1 or −1). Reversing both A/B labels and eta
leaves H algebraically unchanged. Because candidates are scored separately and
never presented as an ordered list, this is not presentation counterbalancing
and does not control positivity, negation, or length bias. The four scenarios
in each family use varied wording, but there is one pair per block (`J = 1`);
wording robustness is not estimated and each effect may depend on its one pair.

## Scoring and interpretation

For a continuation, sum the ordinary log probabilities of **all** its tokens,
in natural-log units. Do not length-normalize, use only the first token, select
favorable candidates, or add an EOS token after outcomes are seen. Tokenize
the prompt and complete prompt-plus-candidate jointly under an exact-prefix
boundary check; a boundary failure is a failed cell, not permission for a
silent fallback.

```text
s(c,e)  = log P(candidate_a | c,e) - log P(candidate_b | c,e)
Delta_p = s(context_p,emoji_b) - s(context_p,emoji_a)
Delta_q = s(context_q,emoji_b) - s(context_q,emoji_a)
H       = eta * (Delta_q - Delta_p)
```

Report all four `s` cells, both deltas, H, and both absent-input scores. A positive
H means an interaction in the author's proposed direction, not necessarily a
reversal. Separately report whether `eta * Delta_p < 0` and
`eta * Delta_q > 0`; only that diagnostic checks the intended directional
crossover of the emoji effects. Neither diagnostic is a human-meaning label.

Full candidate log probability favors some lengths and phrasings. Using the
same strings across the crossed cells removes additive candidate preferences
from the interaction algebra, but does not eliminate context-dependent lexical
or tokenization effects. Keep candidate-token counts, emoji-span counts and
positions, and all four scores visible. The baseline retains token-count or
position mismatches. Any future route-exchange eligibility rule must be separate,
outcome-blind, and explicitly report the excluded denominator.

Summaries give all block effects, six family means, and their equally weighted
mean. No bootstrap, p-value, success threshold, statistical confirmation, or
population-generalizing interval is specified for this first pilot. Positive,
zero, negative, and uncertain cases all remain. A failed cell makes the affected
block incomplete; do not silently average over whichever cells or families
remain.

## Controls and the bounded denominator

| Condition | Input conditions | Candidate-sequence cells | First-pilot status |
| --- | ---: | ---: | --- |
| Two contexts × two emoji × 24 blocks | 96 | 192 | Planned baseline |
| Two contexts × emoji absent × 24 blocks | 48 | 96 | Planned baseline diagnostic |
| Ordinary-word alternatives | Not allocated to the run | 0 | Planned, **not executed** in this baseline; proposed words are recorded per block |
| Non-emoji symbol carriers | Not allocated to the run | 0 | Planned, **not executed**; semantic mapping and neutral-legend design unresolved |
| K/V exchange or other causal intervention | 0 | 0 | Not instrumented or executed by this protocol |
| **Total first-pilot allocation** | **144** | **288** | **24 blocks; six families** |

The ordinary words are not claimed to match token count or human interpretation.
For the symbol control, `+` and `-` are provisional carrier candidates, not a
validated mapping or a task already ready to run. A future design must address
the fact that an explicit legend changes the task. Neither control may be
silently counted as executed. Without them, this pilot cannot support
emoji-specificity or an advantage over generic information carriers.

## Model, acquisition gates, and retention

The [config](../configs/contextual_emoji_output_pilot_v0.json) names the already
used Llama 3.2 3B base BF16 mirror and exact revision
`60a99aaf43164077157d64bf909b7b61143c6a6d`. It permits no download, generation,
training, or route intervention. Input handling follows the prior base-model
choice: no added special tokens, no added BOS, no EOS scoring, and no chat
template. This explicit choice is part of the measurement, not a claim that
all base-model prompting choices are equivalent.

The config also requires artifact-manifest SHA-256
`dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`,
inherited from the [same-revision T21 model pin](../configs/t21_glyph_context_path_pilot_v0.yaml).
The actual local snapshot must match this intended-artifact pin before any
tokenizer or model load. Merely recording the hash of an arbitrary supplied
snapshot is insufficient.

Before a GPU forward, the main task must verify the revised PDF, complete an
independent read-only stimulus critique without model outputs, and bind the
fixed stimulus hash. The runner's preparation receipt then binds the actual
existing snapshot, model/tokenizer artifacts, runtime, and input hashes. The
config leaves snapshot/runtime fields open rather than pretending that a
declared path or package version has been verified. Idle-compute and engineering
preflights remain execution requirements.

One independent agent completed the read-only stimulus critique before the
input hash was fixed. Its check found the orientation signs consistent and
retained all uncertain blocks. This is a design check, not independent human
annotation or semantic validation. It also prompted the explicit distinction
between scoring-label bookkeeping and actual presentation counterbalancing.

The allocation is at most 288 candidate-sequence cells, with a 512-token limit
on each full prompt-plus-candidate sequence, at most 64 candidate tokens within
that total, and a 900-second wall-clock bound. These bounds do not
guarantee successful completion. Preserve planned/completed/failed cell counts
and incomplete blocks if preparation, token boundaries, resource availability,
or runtime limits fail. Do not replace scenarios after observing model output
or rerun favorable variants as if untouched. Any later development revision
must keep this version and explain the change.

## What this pilot can decide next

It can expose malformed prompts, tokenizer incompatibility, absent-control
dominance, candidate-wording sensitivity that remains unmeasured at J = 1,
and weak or inconsistent goal-compatibility interactions. Even clean favorable
results provide only development engineering/behavioral feasibility.

Independent human annotation with `ambiguous`, `both`, and `neither` options,
additional candidate wording, generic-carrier controls, and a separately frozen
new-family confirmation remain necessary before broader claims. Natural-state
bidirectional K/V exchange is a later implementation and experiment with its
own calibration and control requirements. None of its causal conclusions can
be inferred from this output-only baseline.
