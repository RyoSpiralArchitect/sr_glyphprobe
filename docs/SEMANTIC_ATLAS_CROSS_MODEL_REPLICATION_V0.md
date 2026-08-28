# Semantic Atlas Cross-Model Replication v0 (T10)

Status: **pre-acquisition protocol with all nine engineering preflights complete**.
No selected T10 model has been forwarded on the 292-item population.

Japanese companion: [SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.ja.md](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.ja.md)

## Question

T9 established a strong, transport-robust item-retrieval contrast in one
Mistral-7B base checkpoint: glyph representations retrieved their matching
official Unicode names more accurately than literal `U+...` controls in all
eight frozen carrier-distance cells. T10 asks a narrower next question:

> Does that registered item-name alignment replicate in at least three of four
> frozen core model/tokenizer cells after an exact token-count-stratified
> control is required inside every model?

The object is **official-name item alignment**, not human meaning. A positive
T10 result would not show that a model “understands” an emoji, that the effect
is tokenizer-independent, or that it is universal across architectures.

## Why the protocol has two endpoint rows

T8/T9 described layer 31 as `resid_post`, but the implementation selected
`output.hidden_states[layer + 1]`. A synthetic two-layer Mistral audit now
shows that, at the last layer, this expression is the model-final normalized
hidden state: it equals `model.model.norm(last_block_output)` and differs from
the raw last decoder-block output.

T10 therefore records both in each forward:

| Endpoint | Capture | Role |
|---|---|---|
| `returned_final_hidden_state` | `output.hidden_states[-1]` | sole decision-authorized endpoint; exact API-level T9 match |
| `raw_last_decoder_block_output` | forward hook on the final decoder block | registered secondary; cannot rescue the primary |

This is a terminology correction, not a numerical reinterpretation of T9.
The original T9 files remain unchanged and auditable.

## Fixed population and transport

- Population: the same 292 T9 reserve items, ordered by original source index.
- Views: raw glyph, official Unicode name, literal codepoint string.
- Carriers: eight repeats of the single tokens produced by `" a"` and `" |"`
  in each tokenizer.
- Causal readout distances: 1, 2, 4, and 8 carrier tokens after each view.
- Batch size: one unique sequence per forward.
- Forward budget: 1,752 per model, 15,768 across nine model cells.
- Captured vectors: 14,016 per model across two endpoints; 126,144 total.
- Storage: float32 activations in 8-item atomic shards. Raw activations stay out
  of Git and SpiralShare.

Every tokenizer must pass all of the following before freeze:

1. all 292 sequences are non-empty and unique within each view;
2. each carrier unit is exactly one token;
3. appending eight carrier units preserves the complete raw-view prefix;
4. decoding the combined sequence exactly reconstructs the input text;
5. at least 250 items belong to a non-singleton exact token-count stratum.

## Frozen model/tokenizer cells

The roster was selected from immutable public revisions or already complete
furnace artifacts before inspecting any T10 activation. The cells intentionally
mix architecture, release, scale, and instruction status; no factor is isolated.

| Role | Artifact revision | Parameters | Primary role |
|---|---|---:|---|
| `llama32_3b_base_bf16` | `mlx-community/Llama-3.2-3B-bf16@60a99aaf...` | 3.21B | core |
| `qwen25_7b_base_bf16` | `Qwen/Qwen2.5-7B@d1497293...` | 7.62B | core; Qwen ladder anchor |
| `olmo2_1b_base_bf16` | `allenai/OLMo-2-0425-1B@a1847dff...` | 1.48B | core |
| `gemma2_2b_it_bf16` | `google/gemma-2-2b-it@299a8560...` | 2.61B | core; cached gated artifact |
| `qwen25_0p5b_base_bf16` | `Qwen/Qwen2.5-0.5B@060db649...` | 0.49B | registered extension |
| `qwen25_1p5b_base_bf16` | `Qwen/Qwen2.5-1.5B@8faed761...` | 1.54B | registered extension |
| `qwen25_3b_base_bf16` | `Qwen/Qwen2.5-3B@3aab1f19...` | 3.09B | registered extension |
| `smollm2_1p7b_base_bf16` | `HuggingFaceTB/SmolLM2-1.7B@effd688a...` | 1.71B | registered extension |
| `mistral7b_instruct_v03_bf16` | `mistralai/Mistral-7B-Instruct-v0.3@c170c708...` | 7.25B | related-checkpoint extension |

The Qwen 0.5/1.5/3/7B sequence is descriptive. It cannot support a scale law,
monotonicity claim, or causal size effect. The Mistral-Instruct cell is also
descriptive with respect to the known Mistral-base T9 anchor; it is not a
controlled base-versus-instruction comparison.

## Observed zero-forward engineering preflight

All nine exact revisions passed the static artifact and tokenizer gate without
loading model weights or making a candidate forward. The artifact audit
requires at least one nonempty weight file and resolves every file named by
every `*.index.json` `weight_map`. This condition rejected an initially
incomplete Qwen 3B snapshot whose index named an absent second shard; the
receipt below was generated only after the same immutable revision completed.

| Model cell | Present weight files / index-referenced files | Exact-stratum items | Eligible strata | Artifact manifest SHA-256 |
|---|---:|---:|---:|---|
| `llama32_3b_base_bf16` | 2 / 2 | 281 | 25 | `dc5b61a2c4aa...` |
| `qwen25_7b_base_bf16` | 4 / 4 | 284 | 22 | `bd8ef40517ce...` |
| `olmo2_1b_base_bf16` | 2 / 2 | 281 | 25 | `d92749838283...` |
| `gemma2_2b_it_bf16` | 2 / 2 | 284 | 16 | `1b2b83416e64...` |
| `qwen25_0p5b_base_bf16` | 1 / no index | 284 | 22 | `c860aa324659...` |
| `qwen25_1p5b_base_bf16` | 1 / no index | 284 | 22 | `cb56a7e1865b...` |
| `qwen25_3b_base_bf16` | 2 / 2 | 284 | 22 | `cca372c88da2...` |
| `smollm2_1p7b_base_bf16` | 1 / no index | 287 | 14 | `aaecf4014031...` |
| `mistral7b_instruct_v03_bf16` | 4 / 3 | 285 | 20 | `d20865c47632...` |

Thus every cell exceeds the frozen minimum of 250 exact-stratum items; the
observed range is 281--287. Full hashes, file counts, byte counts, token
sequences, carrier checks, and strata are retained in the nine JSON receipts.

## Per-model primary: an intersection-union test

For each carrier-distance cell, each of the three view matrices is centered
separately over items and each row is L2-normalized. The forward retrieval
contrast is

```text
top1(glyph -> matching official name)
  - top1(glyph -> matching U+ literal)
```

The cell-robust statistic is the minimum contrast over all eight cells. Each
model has two required components.

### A. Unrestricted component

- Uses all 292 items as queries and candidates.
- One random permutation of official-name correspondence is shared by all
  eight cells in each draw.
- Codepoint correspondence and all representation matrices stay fixed.

### B. Exact tokenization-matched component

Each item receives the exact key

```text
(glyph token count, official-name token count, codepoint-literal token count)
```

Items in singleton strata are omitted from component B only. Centering,
normalization, queries, and candidates are recomputed inside the eligible
subset. The official-name correspondence is permuted only within each exact
stratum, with one common stratified permutation across all eight cells.

For both components:

- 19,999 deterministic randomization draws;
- p-value `(1 + exceedances) / 20,000`;
- practical floor: observed minimum contrast at least 0.02.

The model-level p-value is `max(p_A, p_B)`. A model passes its raw registered
rule only when this IUT p-value is at most 0.05 **and** both practical floors
pass. Neither component can compensate for the other.

## Sole cross-model primary

The four core model IUT p-values enter a Bonferroni partial-conjunction test
for at least `r = 3` of `m = 4` cells:

```text
p_PC = min(1, (m - r + 1) * p_(r)) = min(1, 2 * p_(3))
```

where `p_(3)` is the third-smallest core model IUT p-value. The positive rule
requires both:

1. `p_PC <= 0.05`; and
2. at least three core cells pass both practical floors.

Authorized positive wording is limited to:

> At least three of four frozen core model/tokenizer cells replicate under the
> registered rule.

The nine exact model-cell IUT p-values also form one Holm family for bounded
cell-specific statements. Those rejections are secondary to the partial
conjunction and cannot rescue it.

## Registered secondary outputs

- raw last-block endpoint profile and its difference from the returned state;
- Qwen four-point size profile;
- complete carrier/distance Top-1, MRR, cosine-margin, and centered linear CKA;
- token-count histograms and exact-stratum coverage;
- per-model latency, peak memory, and artifact size;
- descriptive comparison with the known T9 Mistral-base result.

No secondary output authorizes post-outcome model, endpoint, item, carrier,
distance, threshold, seed, or stratum selection.

## Outcome branches

### Branch 1: cross-cell replication passes

Report the exact partial-conjunction result, core practical-pass count, and
Holm-qualified model cells. The next study may move to causal localization,
but only in cells that passed both tokenization components. The claim remains
about official-name item alignment.

### Branch 2: only some exact cells pass

Report the bounded Holm-qualified cells and the failed cross-cell primary.
Architecture/tokenizer heterogeneity becomes the next object; the successful
cells do not license a general claim.

### Branch 3: unrestricted passes but matched fails

Treat tokenization structure as a live explanation. This is a useful negative
result and blocks causal interpretation of the alignment contrast.

### Branch 4: neither component replicates

Treat T9 as a bounded Mistral-base result. T11 may still explore unusual glyphs,
but it must not inherit a cross-model semantic premise from T10.

## Freeze and execution gates

Before the first selected-model forward, the committed freeze must bind:

- this protocol, its Japanese companion, implementation, and synthetic tests;
- all five T9 source receipts by SHA-256;
- the endpoint-semantics audit;
- all nine exact model artifact manifests and tokenizer sequence receipts;
- the joint engineering preflight, primary rule, seeds, thresholds, and roster.

Execution then proceeds one model at a time. The runner checks furnace
contention before model load and before every 8-item shard, yields if another
GPU process appears, never reacquires a completed shard, and fails closed on an
incomplete staging directory. Per-model summaries compute both endpoints;
joint randomization uses only the frozen primary endpoint.

## Claim boundary

Even the strongest positive branch does **not** establish:

- human or compositional emoji meaning;
- tokenizer-independent evidence;
- independent replications;
- a causal or mechanistic circuit;
- behavioral steering or generation effects;
- a base/instruction effect;
- a scale law or monotonic size trend;
- architecture-wide or universal model generality;
- completion of the Phase I paper gate.

T10 is the bridge from one-checkpoint confirmation to a bounded cross-cell
result. Semantic decomposition remains a later hypothesis, not a T10 outcome.
