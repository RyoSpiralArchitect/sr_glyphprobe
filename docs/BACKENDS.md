# Backend capability boundary

[Japanese / 日本語](BACKENDS.ja.md) · [E2 Stage-A result](LLAMA32_3B_MLX_VALIDATION_RESULTS.md)

The CLI is shared, but backend names do not imply that two runtimes expose the
same numerical object. Read `capabilities.json`, `receipt.json`, and the backend
sections below before comparing runs.

## Internal backends

### TransformerLens (`lens`)

`lens` is the canonical hook path. It uses TransformerLens hook names and prefers
`TransformerBridge.boot_transformers`, with a version-compatible
`HookedTransformer.from_pretrained` fallback. Loader arguments, resolved dtype,
layer count, width, loader path, and model receipt are recorded.

### Transformers/PyTorch (`transformers`)

`transformers` uses `AutoModelForCausalLM` and PyTorch module hooks. Decoder
blocks are discovered conservatively. `resid_post` means decoder-block output.
`resid_pre`, `attn_out`, and `mlp_out` depend on model-family structure and must
not be compared across architectures without a model-specific parity receipt.
The selected public dtype keyword, resolved dtype, loader arguments, and local
model-artifact manifest are recorded.

### MLX-LM (`mlx`)

`mlx` is the Apple-silicon path. It temporarily proxies selected decoder blocks,
edits or captures the full-sequence decoder-block output, evaluates the complete
lazy graph, and copies results to NumPy. One backend instance must not execute
concurrent forwards while those proxies are installed.

The current implementation supports only `resid_post` capture and intervention.
Requests for `resid_pre`, `attn_out`, `mlp_out`, or attention weights fail closed.
Generation is not exposed. Quantized MLX models require `dtype: auto`; they need
their own parity validation before scientific use.

Forward logits and hidden-state capture can be inspected without a parity
receipt. Activation intervention is different: the capability is advertised and
the operation is allowed only after the backend loads a SHA-256-pinned receipt
whose status, model, revision, dtype, site, current source-tree hash, stable model
identity, parity gate, and speed gate all match. A missing, changed, stale, or
failed receipt therefore disables or rejects activation patching.

The shipped validated cell is deliberately narrow:

- model: `openai-community/gpt2`;
- revision: `607a30d783dfa663caf39e06633721c8d4cfcd7e`;
- dtype/device: FP32 on the MLX Metal GPU;
- site: `resid_post`;
- intervention layers: 2, 4, 7, and 9;
- parity workload: four sealed prompt-length cases, exact token IDs, baseline and
  intervened activations/logits, zero-hook behavior, intervention-delta direction
  and magnitude, and synchronized end-to-end latency.

This receipt does not validate other models, revisions, dtypes, sites, hardware,
prompt distributions, or quantized cells. `model_receipt` records MLX/MLX-LM
versions, resolved device/dtype, block path, quantization metadata, model locator,
and a path-independent file manifest for the resolved model artifact.

#### Failed Llama 3.2 3B BF16 Stage-A cell

The Llama 3.2 3B v1 engineering attempt stopped at the first MLX BF16-to-NumPy
baseline export. V2 retained native-BF16 model execution but cast MLX BF16
arrays to `mx.float32` immediately before NumPy export. That narrow bridge fix
allowed the isolated Transformers/MPS and MLX phases to complete, but the
receipt records `status: validation_failed` and `scientific_result: false`.

The pinned v2 cell passed 33 / 60 parity checks. Tokenization/determinism and
exact zero-hook behavior each passed 10 / 10, while composite deltas and
intervention fidelity each passed 0 / 10. Aggregate median latency was
132.127833 ms for Transformers/MPS and 230.138000 ms for MLX, so the
machine-local speed gate also failed. This receipt does not authorize activation
intervention for the Llama cell. Forward-logit and hidden-state capture remain
inspectable under the general boundary above, but capture is not a substitute
for a passing intervention receipt.

Receipts are also source-tree-hash bound. An older receipt remains historical
evidence for the exact implementation it records; after backend source changes,
it cannot authorize activation patching in the current source tree unless every
required identity and gate matches again. Do not reinterpret the preserved v1
failure record or the failed v2 receipt as current authorization.

See the [complete v2 result](LLAMA32_3B_MLX_VALIDATION_RESULTS.md),
[frozen protocol](LLAMA32_3B_MLX_VALIDATION_PROTOCOL.md),
[v1 failure record](../validation/mlx_llama32_3b_bf16_parity/attempt_01_failure.json),
and [v2 receipt](../validation/mlx_llama32_3b_bf16_parity_v2/receipt.json).

### Deterministic mock (`mock`)

`mock` is a deterministic synthetic residual stream for CI and end-to-end
plumbing. It is never model evidence.

## OpenAI-compatible serving backends

`vllm`, `llamacpp`, `ollama`, `lmstudio`, and `openai` share a generation adapter.
Standard compatible endpoints do not expose residual streams or arbitrary
activation patching, so these backends are stamped `surface-observational-only`.

The adapter runtime-probes top-logprob support. Compatibility retries remove
unsupported request fields while preferring variants that retain logprobs. A
resumed run reconstructs stored neutral baselines rather than regenerating them.

## Cross-backend comparisons

A shared model identifier is not proof of equivalence. Tokenizer revisions, chat
templates, fused kernels, quantization, GGUF conversion, weight processing, and
device precision can all change outputs. Bind every comparison to the exact
backend, model-artifact manifest, implementation hash, runtime receipt, and an
explicit parity workload. The MLX parity receipt is a backend-selection gate, not
a scientific result about glyphs.
