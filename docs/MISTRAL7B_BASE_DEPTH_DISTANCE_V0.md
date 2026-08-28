# Mistral 7B base depth-by-distance v0

[日本語](MISTRAL7B_BASE_DEPTH_DISTANCE_V0.ja.md) · [T6 results](MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.md) · [Roadmap](ROADMAP.md)

Status: **prospective freeze in preparation; zero T7 model forwards**.

## Why this cell

T6 did not pass its all-depth distance-attenuation endpoint. Its complete
secondary profiles nevertheless showed a specific descriptive shape in the
Mistral 7B Instruct cell: strong attenuation at the first fixed depth and much
flatter contrasts later. A slot-scramble transform would only reindex T6's
existing synchronized permutation null, so repeating those 400 forwards would
add no information.

T7 instead freezes one previously unobserved cell:
`mistralai/Mistral-7B-v0.3@caa1feb…`. It is the base checkpoint from the same
v0.3 generation as the T6 Instruct model, with the same architecture size and
an expected matching tokenizer roster. The base outcome has not been viewed.

The model and endpoint were chosen after T6. T7 is therefore prospective only
for this base cell's unseen outcomes. It is not an independent confirmation,
and the one base/instruct pair cannot identify an instruction-tuning effect.

## Fixed design

The public five-family by ten-slot emoji panel, two eight-token carriers
(`" a"` and `" |"`), distances `[1, 2, 4, 8]`, and `resid_post` depths
`[0, .25, .5, .75, 1]` are unchanged from T6. The resolved Mistral layers are
`[0, 8, 16, 24, 31]`. Each complete glyph-plus-carrier string is forwarded at
each readout position, for exactly 400 forwards and 2,000 captured vectors.

There is no intervention, generation, behavior scoring, or protected-target
access.

## Primary endpoint

At every carrier, distance, and depth, family means are removed and the fixed
matched-slot fraction is computed:

`SS_slot / (SS_slot + SS_interaction)`.

The primary decision is one intersection-union test:

1. distance-1 recurrence is the equal-weight mean over both carriers and all
   five depths;
2. at each depth, attenuation is the equal-carrier distance contrast with
   weights `[0.375, 0.125, -0.125, -0.375]`;
3. the interaction statistic is attenuation at depth 0 minus the equal-weight
   mean attenuation at the four later depths;
4. the IUT p-value is the larger of the recurrence and interaction p-values.

The synchronized null independently permutes matched-slot labels inside the
four non-reference families across 19,999 PCG64 draws with seed `2026082801`.
The single IUT is tested at alpha 0.05; there is no multiplicity adjustment.
Passing requires both components. Per-depth, per-carrier, tail, original-T6,
and base/instruct comparisons are secondary and cannot replace a failed IUT.

## Artifact and zero-forward gate

The official public model revision is fixed to
`caa1feb0e54d415e2df31207e5f4e273e33509b1`. The local artifact intentionally
excludes the duplicate 14.5 GB `consolidated.safetensors` and includes the
Transformers three-shard index plus tokenizer/config files. Its exact file
manifest, architecture dimensions, parameter count, and tokenizer sequences
must be recorded by a zero-forward preflight before the freeze commit.

Immediately before model loading, `spiral status` must again show no competing
GPU process. The runner then verifies the public freeze, local artifact hash,
runtime versions, CUDA device, BF16 parameter dtype, model class, block path,
token roster, carrier identities, and round trips before the first forward.

## Registered interpretations

The four exhaustive branches are: both components pass; recurrence only;
interaction only; or neither. Every branch retains the one fixed model and all
40 carrier-by-distance-by-depth rows.

Even a passing IUT would support only a fixed depth-dependent observational
profile in this selected unseen base cell. It would not establish semantic
content, mechanism, causality, behavior, monotonic decay, persistent memory,
tokenizer causality, an instruction-tuning effect, model generality,
independent confirmation, or closure of a Phase I paper gate.
