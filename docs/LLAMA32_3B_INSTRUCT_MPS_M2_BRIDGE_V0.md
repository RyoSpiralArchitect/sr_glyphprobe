# Llama 3.2 3B Instruct M2 bridge v0

[日本語](LLAMA32_3B_INSTRUCT_MPS_M2_BRIDGE_V0.ja.md) · [Milestone 2 protocol](MILESTONE2_PROTOCOL.md) · [Scale option space](SCALE_FALSIFICATION_OPTION_SPACE.md)

Protocol ID: `glyphprobe-llama32-3b-instruct-mps-m2-bridge-v0`

## Status and question

Status is `static_freeze_pending_publication`. No language-model forward in this
study is authorized until the static manifest is committed and pushed, the
zero-forward preflight passes from that exact public commit, and the preflight
receipt is committed as the only subsequent file.

This bounded bridge asks whether the GPT-2 Milestone 2 colored-shape advantage
appears in one pinned Llama 3.2 3B Instruct Transformers/MPS BF16 cell after
matching the Llama tokenizer structure as tightly as its finite input inventory
permits. It is not a scale curve: model lineage, tokenizer, instruction tuning,
backend, and numerical precision all change relative to GPT-2.

The 24 targets are the already explored first 24 `prestage_targets`. Therefore
the study is exploratory even though its grid and decision rule are frozen
before its first outcome. P2 and retired C1 are outside every executable,
preflight, and analysis input surface.

## Tokenizer-only control construction

The original GPT-2 control panels do not transfer unchanged to the pinned Llama
tokenizer:

- panel A passes the raw and all 16 contextual-wrapper matching checks;
- `🟁` in panel B is two tokens rather than three; and
- `🟥` in panel C is two tokens rather than three.

Two result-blind searches were then exhausted before any model outcome:

1. all 3,264 scalars in the fixed symbol ranges, under category, name,
   round-trip, three-token, and `[9468,253]` prefix filters; and
2. all 128,000 base-vocabulary final-token completions after `[9468,253]`,
   restricted to one emoji grapheme and exact re-encoding.

Both searches returned zero unused candidates. The original compatible pool
therefore contains 25 distinct dominant-prefix glyphs for 27 required slots.
By the pigeonhole principle at least two placements must be reused.

The v2 construction attains that lower bound with a fixed cyclic donor rule:

- panel A lends its lowest compatible scalar `🟀` (`U+1F7C0`) to panel B;
- panel B lends its lowest compatible scalar `🟄` (`U+1F7C4`) to panel C.

Final pairwise overlaps are A–B = 1, A–C = 0, and B–C = 1. All three panels
match the colored-shape panel on item count, raw three-token/prefix histogram,
and every full structural histogram in all 16 wrappers. They are not three
independent panels. Any interpretation must preserve that dependence.

## Fixed model and runtime

| Field | Frozen value |
|---|---|
| Model | `meta-llama/Llama-3.2-3B-Instruct` |
| Revision | `0cb88a4f764b7a12671c53f0838cd831a0843b95` |
| Artifact | 8 files, 6,434,691,515 bytes, manifest `c698f962…ecf6` |
| Architecture | 28 layers, width 3072, 3,212,749,824 parameters |
| Backend | raw Transformers on MPS |
| Runtime dtype | BF16 |
| Network | Hugging Face and Transformers offline |
| Runtime alias | `/private/tmp/glyphprobe-llama32-3b-instruct-v0` |

The alias is a fixed non-user-specific symlink created only after the launcher
verifies the complete path-independent artifact manifest. The real storage path
is not recorded. The earlier same-artifact synthetic screen found MPS faster
than MLX for this 3B checkpoint, but intervention-delta parity was incomplete.
Accordingly this study uses MPS; it makes no backend or speed claim.

ChatGPT, Codex, and WindowServer may remain active during execution. That may
change latency and failure risk, not the prespecified estimand. No timing number
from this run is eligible for a performance claim.

## Fixed four-panel grid

The four processes run in this order without intermediate outcome inspection:

1. colored-shape primary panel;
2. minimum-overlap null A;
3. minimum-overlap null B;
4. minimum-overlap null C.

Every process uses:

- all 16 source wrappers and the first 24 reused prestage targets, four in each
  of six target groups;
- normalized depths `0.20` and `0.40`, resolving to layers 5 and 11 in the
  28-layer model;
- `resid_post`, `last_nonpad`, RMS-normalized strength `0.05`;
- direction seeds 101, 211, and 307, averaged inside targets;
- eight random directions per layer and an exact zero-hook control;
- no sign flip, neutral direction, label shuffle, SAE, iso-KL, or generation;
- 96-dimensional CountSketch fingerprints with seed 8675309.

Runs are isolated sequential processes. Resume is forbidden. A failure or
interruption publishes a failure receipt and retires v0 rather than allowing a
selective rerun.

## Frozen exploratory endpoints

For each panel, layer, target, and seed, the analysis uses the Milestone 2
leave-one-target-group-out condition-identification score. Every bootstrap
replicate jointly resamples four targets with replacement inside each of the six
groups and rebuilds every panel/condition prototype from the other five groups.
Direction seeds remain nested estimates.

Two layer-5 endpoints are mandatory:

```text
D_ensemble[t] = S_primary[t] - median(S_A[t], S_B[t], S_C[t])
D_A[t]        = S_primary[t] - S_A[t]
```

`D_A` is the fully disjoint panel-A sensitivity. The primary exploratory status
is `exploratory_bridge_pattern_observed` only if both two-sided 95% percentile
bootstrap lower bounds at layer 5 are strictly greater than the existing
Milestone 2 practical threshold `delta = 0.06`. The bootstrap has 20,000
replicates and seed 20260828.

Layer 11 is a prespecified secondary comparator and cannot rescue layer 5.
Random-control run summaries, target-group descriptions, individual glyphs, and
all other values are secondary. No p-value, multiplicity-adjusted hypothesis
status, equivalence status, or confirmatory label is produced.

## Claim boundary and landing patterns

A positive primary status supports only this wording:

> In one prospectively frozen Llama 3.2 3B Instruct Transformers/MPS BF16 cell,
> the colored-shape target-identification score exceeded both the
> minimum-overlap tokenizer-matched ensemble and its fully disjoint panel-A
> sensitivity on 24 reused exploratory targets.

A failed criterion is a clean negative bridge under the tested estimand. A
layer-11-only effect is also negative because layer 11 is non-rescuing.

Neither result establishes monotonic scaling, tokenizer independence, emoji
semantics, an internal circuit, causal localization, generation behavior, or
independent target generalization. The two null overlaps must always be stated.

## Publication sequence

1. Commit and push this protocol, its Japanese pair, configs, panels, scripts,
   tests, negative-search receipts, and static manifest.
2. In a clean isolated mac1 worktree, run the zero-model-forward preflight.
3. Pull its hash-verified receipt, commit it as the only post-freeze file, and
   push again.
4. Update the isolated worktree to that public commit and run all four cells
   sequentially without reading intermediate outputs.
5. Run the frozen analyzer once only after the execution receipt authorizes it.
