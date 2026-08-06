# GlyphProbe v1 scientific contract

[Japanese / 日本語](SCIENTIFIC_CONTRACT.ja.md)

## Question

GlyphProbe v1 asks whether fixed glyph-derived activation directions leave
reproducible output-space fingerprints after intervention magnitude, clipping,
source wrappers, target cases, and random-direction controls are made explicit.

It does not begin by asking what an emoji "means" inside a model. Semantic and
mechanistic interpretation is withheld until numerical and geometrical
preconditions survive blind screening and later targeted interventions.

## Unit of analysis

The principal sampling clusters are target prompts. Source-direction seeds are
repeated estimates produced from sealed wrapper subsets; they do not create
independent target observations. Generation seeds on the surface-server path are
sampling replicates and remain nested within targets.

## Default estimands

For each glyph, layer, strength, and source-direction seed, the internal path
records:

1. achieved perturbation-to-target RMS ratio and clipping;
2. activation fidelity at the patched site;
3. next-token distribution displacement;
4. a unit-normalized CountSketch of the full-vocabulary logit delta;
5. held-out target fingerprint separation;
6. separation relative to panel-span-orthogonal random directions;
7. a within-target glyph-label permutation null;
8. cross-seed fingerprint stability;
9. color, shape, and interaction geometry for the balanced default panel.

The zero-vector hook is executed explicitly. Reusing an unhooked baseline would
not detect a hook that mutates tensors, changes dtype, or addresses the wrong
position.

## Claim levels

**P0 — plumbing:** deterministic mock and adapter tests pass.

**P1 — scalar control:** requested RMS, achieved RMS, clipping, and zero-hook
no-op checks pass.

**P2 — reproducible fingerprint candidate:** same-glyph held-out and cross-seed
fingerprints exceed cross-glyph and random-direction controls across a prespecified
matrix.

**P3 — structured geometry candidate:** factor or interaction structure repeats
across target splits, direction seeds, and strengths.

**C1 — targeted causality:** a later experiment identifies components or paths
whose patching, ablation, or restoration selectively changes the candidate effect.

The harness can screen through P3. A stage label must be earned by each run; it is
not inherited from the software. No default artifact authorizes C1 language, and
P2/P3 evidence does not by itself establish glyph semantics or a mechanism.

## Nulls and controls

The bundled controls address different failure modes and are not interchangeable:

- neutral glyph: generic glyph/emoji presence;
- panel centering: shared panel component;
- zero hook: intervention-machinery side effects;
- random span-orthogonal directions: generic sensitivity outside the panel span;
- sign flip: local odd symmetry and saturation;
- dose grid: monotonicity and clipping;
- iso-KL arm: approximately equal output-distribution displacement, only when run;
- within-target label permutation: label identity while preserving target structure;
- tokenization receipt: raw segmentation and wrapper-length mismatch;
- backend parity: implementation/runtime disagreement, not a glyph null.

Absence of an optional arm is missing evidence, not a negative result. A minimum
permutation p-value is a finite-grid screening floor, not exact zero probability.

## Escalation criteria

A candidate is worth finer causal work only when it survives multiple target
clusters, multiple separately estimated source directions, at least two random
directions, a positive dose grid, explicit scalar-balance receipts, and a backend
cell whose capability and parity receipts match the run. The next experiments are
component patching, path patching, ablation/restoration, natural-language
projection removal, checkpoint emergence, and cross-model replication.

## Phase I publication goal

Phase I ends with an English-language paper, supported by paired English/Japanese
repository documentation. The paper will report methods, prespecified cells,
heterogeneity, negative results, and unexecuted controls; bind every reported run
to source, configuration, runtime/dependency, model-artifact, and validation
receipts; and keep pre-causal evidence separate from causal or semantic claims.
