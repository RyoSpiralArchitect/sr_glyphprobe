# T16-UTF-X1 scale and sequence-variant stress test

[日本語](T16_UTF_SCALE_VARIANTS_V1.ja.md) · [Parent T16-UTF protocol](T16_UTF_IDENTITY_MIXING_V0.md)

T16-UTF-X1 is a deliberately large exploratory sequel to T16-UTF. It asks
whether the earlier separation between exact-string repetition, within-family
mixing, and cross-family mixing survives much longer sequences and a broader
set of already-frozen model/tokenizer cells. It also separates three effects
that the parent experiment did not identify: item order, separator choice, and
the position of one exact UTF anchor.

No T16-UTF-X1 activation outcome may be opened before the complete design,
tokenizer receipts for all nine roles, and the final execution manifest are
committed and pushed.

## Frozen grid

The source panel remains the same 24 exact strings: four items in each of six
Unicode construction families. Every cell uses four fixed wrappers and four
rotations.

The stress test has three disjoint lanes:

- **Scale:** `n = 1, 2, 3, 4, 5, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192,
  256, 384, 500`, with exact clones, within-family cycles, and cross-family
  cycles.
- **Order:** `n = 8, 16, 32, 64, 128, 256`, with within-family and cross-family
  multisets rendered as forward, reverse-tail, blocked-tail, interleaved-tail,
  and two frozen deterministic shuffles. The first item and exact item multiset
  stay fixed within every paired comparison.
- **Position:** the same six lengths, with exactly one anchor placed first,
  middle, or last against a within-family or cross-family background. All three
  positions share the exact same item multiset.

Order and position use five separators: none, ASCII space, comma-space,
newline, and ASCII pipe. This yields 57,312 factorial records per model and
515,808 across nine model/tokenizer cells. The run is split into 11 atomic
chunks per model so a contention yield never invalidates a completed chunk.

## Model cells and endpoint

The nine roles were already frozen and runtime-preflighted in T10/T13: four
Qwen2.5 sizes, Llama 3.2 3B, OLMo 2 1B, SmolLM2 1.7B, Gemma 2 2B IT, and
Mistral 7B Instruct v0.3. Shared training data, tokenizer ancestry, and model
families mean these are bounded cells, not independent replications.

At normalized depths 0.25, 0.50, 0.75, and 1.0, the endpoint is the raw decoder
block output at the final common wrapper token. There is no generation and no
intervention.

## Tokenization and paired controls

Before the final freeze, every prompt is tokenized locally from its pinned
snapshot. The receipt binds full token IDs, token counts, full-prompt token
multiset hashes, artifact identity, and the maximum context length per role.
Any prompt above 8,192 tokens fails closed.

Exact item-multiset matching is a Unicode-string control, not a tokenizer
control. Analysis therefore reports both exact token-count match rates and the
stronger exact full-prompt token-multiset match rates for every paired order and
position contrast.

## Descriptive endpoints

- Scale: clone growth from `n=1`, within-family displacement from the same-`n`
  clone, cross-family displacement from that clone, and cross-minus-within.
- Order: cosine displacement from forward-tail order at fixed family, `n`,
  separator, wrapper, anchor, and exact item multiset.
- Position: displacement from anchor-first at fixed background, `n`, separator,
  wrapper, and exact item multiset.
- Separator: displacement from no separator at fixed item order and all other
  factors.

The principal descriptive unit is system × rotation × wrapper (96 units per
model-depth cell). Equal-tailed 95% intervals use 10,000 system-stratified
bootstrap replicates. Detailed per-`n` medians are reported without creating a
post-outcome binary gate.

## Claim boundary

T16-UTF-X1 can describe conditional hidden-state geometry and test whether a
pattern is stable across this frozen grid. It cannot establish
tokenizer-independent Unicode composition, emoji meaning or understanding, a
causal circuit, an instruction-tuning effect, a scaling law, independent model
replication, or architecture/model-population generality.

Protected P2/C1 target banks are not opened, tokenized, sampled, or used.

## Execution surface

```bash
python scripts/t16_utf_scale_variants_v1.py audit-design
python scripts/t16_utf_scale_variants_v1.py preflight-role \
  --role qwen25_0p5b_base_bf16 \
  --output validation/t16_utf_scale_variants_v1/tokenizers/qwen25_0p5b_base_bf16.json
python scripts/t16_utf_scale_variants_v1.py aggregate-preflight \
  --directory validation/t16_utf_scale_variants_v1/tokenizers \
  --output validation/t16_utf_scale_variants_v1/tokenizer_preflight.json
python scripts/t16_utf_scale_variants_v1.py freeze
python scripts/t16_utf_scale_variants_v1.py audit-freeze --require-pushed
```

CUDA acquisition uses `run-role`, yields with exit code 75 when a foreign GPU
process appears, and resumes only from completed chunk boundaries. Raw hidden
arrays remain on the furnace; only compact receipts and analysis are admitted
to Git.

An execution canary from freeze commit `7a99494` exposed an unsafe padded-token
budget before integrated scientific opening: Qwen2.5 0.5B completed three
chunks, then the allocator reported failed 3.97 GB and 7.74 GB requests during
the next chunk. No activation value was inspected. That run root is retained as
engineering-invalid evidence and cannot contribute scientific results. The
scientific grid is unchanged; the amended freeze sets a conservative 4,096
padded-token budget for every role and starts from a new empty run root.
