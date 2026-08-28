# Multifamily dense CUDA carrier-distance v0

[日本語](MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0.ja.md) · [T5 results](MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.md) · [Roadmap](ROADMAP.md)

Status: **prospective freeze with zero T6 model forwards**. The freeze becomes
complete only in the public commit that binds this document to the executable,
config, tests, preflight, model manifests, and checksum manifest.

## Question

T5 found distance-1 recurrence in the Llama and OLMo component statistics but
no model passed the preregistered conjunction of distance-1 recurrence and a
positive fixed carrier-distance attenuation contrast. T6 asks whether that
same complete observational endpoint recurs in four locally complete dense
Transformers/CUDA cells on the furnace.

The roster was selected after T5 was known. T6 is therefore a prospective
replication only with respect to its own unseen outcomes. It is not an
independent confirmation of T5 and cannot turn the selected 2B/4B/7B/12B cells
into an inference about scale.

## Frozen model roster

| Role | Exact artifact | Parameters | Layers × width | Raw glyph tokens | Model-output vocabulary |
|---|---|---:|---:|---|---:|
| `gemma2_2b_it` | `google/gemma-2-2b-it@299a856…` | 2,614,341,888 | 26 × 2,304 | 50 × one token | 256,000 |
| `gemma3_4b_it` | `google/gemma-3-4b-it@093f9f3…` | 4,300,079,472 | 34 × 2,560 | 49 × one, 1 × four | 262,208 |
| `mistral7b_instruct_v03` | `mistralai/Mistral-7B-Instruct-v0.3@c170c70…` | 7,248,023,552 | 32 × 4,096 | 49 × five, 1 × two | 32,768 |
| `gemma3_12b_it` | `google/gemma-3-12b-it@96b6f1e…` | 12,187,325,040 | 48 × 3,840 | 49 × one, 1 × four | 262,208 |

Every snapshot is local and complete under its pinned full-file manifest. The
three incomplete cache refs for Llama 3 8B base, Llama 3 8B Instruct, and Gemma
2 2B base are excluded before any T6 activation outcome. All four selected
models are instruction-tuned; no chat template or special token is added.

Gemma 3 4B and 12B share the exact observed tokenizer roster. Their pair is a
useful descriptive comparison but remains one pair, not a scale sample.

## Zero-forward tokenization and artifact preflight

The engineering preflight used zero model forwards, interventions, generation
calls, and protected-target reads. It fixed:

- every raw 50-item token sequence through an ordered SHA-256;
- the full token-count histogram and common-prefix sequence per tokenizer;
- carrier token identity for eight repeated `" a"` and `" |"` units;
- exact raw-prefix preservation, combined-sequence SHA-256, and 50/50 decode
  round trips;
- the model revision, full artifact manifest, indexed parameter count,
  architecture dimensions, and expected BF16 execution contract.

The public preflight does not contain machine-local model paths.

## Fixed input and capture

T6 reuses the public 5-family × 10-slot panel. For every glyph and carrier, the
complete raw-glyph-plus-eight-carrier-token input is forwarded independently at
distances 1, 2, 4, and 8. The input and current carrier-token identity do not
change across those four reads; only the captured position changes.

`resid_post` is captured at five depth fractions using
`min(num_layers - 1, floor(fraction * num_layers))` for fractions
`[0, .25, .5, .75, 1]`. Gemma 3 uses the explicitly frozen
`model.language_model.layers` decoder-block path; the other cells use
`model.layers`.

There are 400 forwards and 2,000 captured vectors per model, or 1,600 forwards
and 8,000 vectors in the complete four-model study. There is no activation
intervention, generation, behavior scoring, or protected target access.

## Primary endpoint and multiplicity

Within each carrier, distance, and depth, vectors are arranged as family ×
matched slot. After removing each family mean, the slot fraction is

`SS_slot / (SS_slot + SS_interaction)`.

For each model:

1. criterion A is the equal-weight distance-1 mean over both carriers and all
   five depths;
2. criterion B is the equal-weight log-distance contrast with weights
   `[0.375, 0.125, -0.125, -0.375]` at distances `[1, 2, 4, 8]`;
3. the model-level intersection-union p-value is `max(p_A, p_B)`.

The null independently permutes slot labels inside four non-reference families
while synchronizing each draw over carrier, distance, and depth. There are
19,999 PCG64 draws with seed `20260831`. The four model-level IUT p-values form
one Holm family at FWER 0.05. Only those four adjusted decisions have authority.

Carrier-, distance-, depth-, tail-, Gemma-pair-, timing-, and T5-comparison
outputs are secondary. They cannot replace a failed model-level conjunction.

## Registered outcome branches

- all four dense cells pass;
- exactly the Gemma 3 4B/12B pair passes;
- only Gemma 3 12B passes;
- another nonempty rejection set passes;
- no dense cell passes.

Every branch retains all four models and all 160 profile rows. A failed cell is
not replaced. A favorable carrier, distance, depth, or model pair is not
promoted after outcomes are visible.

## Operational start gate

Before the first T6 model load, the runner must recheck `spiral status` and
observe no competing compute process. The fresh `resource:furnace` notice must
also have a natural receiver-owned task lifecycle surface in an applicable
subscribed session. Canonical publication, watcher arrival, or an OS popup alone
does not satisfy that second gate. No synthetic boundary probe, hook-trust
bypass, process interruption, or self-created acceptance is permitted.

If either condition is absent, tokenizer and artifact preflight may continue,
but T6 model loading and forwards remain at zero.

## Runtime and execution

The frozen execution cell is PyTorch `2.13.0+cu132`, Transformers `5.15.0`,
BF16 CUDA on one NVIDIA GeForce RTX 5090, with local-only artifact loading. Each
model runs in its own process so the prior model is released before the next
model loads.

After the public freeze commit is transferred and audited, the role-bound form
is:

```bash
python scripts/multifamily_dense_cuda_carrier_distance_v0.py audit-freeze
python scripts/multifamily_dense_cuda_carrier_distance_v0.py tokenizer-preflight \
  --model-label <role> --model-path <local-snapshot>
python scripts/multifamily_dense_cuda_carrier_distance_v0.py run \
  --model-label <role> --model-path <local-snapshot> --output <new-output-dir>
```

The four sealed runs are analyzed only in the fixed role order. Outputs contain
activation arrays, complete observations, scrubbed runtime/model receipts,
per-bundle SHA-256 ledgers, 160 secondary profile rows, and one joint analysis
receipt.

## Claim boundary

T6 can report which of its four predeclared model-level IUTs survive Holm
correction. It cannot establish semantic content, a causal mechanism, generated
behavior, tokenizer equivalence or causality, monotonic decay, disappearance,
duration, persistent memory, base/instruct equivalence, backend parity, node or
precision effects, model-scale effects, direct magnitude ordering,
confirmation, or closure of a Phase I paper gate.
