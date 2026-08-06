# GlyphProbe v1 validation

[Japanese / 日本語](VALIDATION.ja.md)

## Release test suite

The current release environment completed all **76 tests**. They cover strict
configuration resolution and overrides, relative validation-receipt resolution,
capability boundaries, MLX receipt- and layer-gated activation patch advertisement,
fail-closed readiness inputs, public-bundle path and receipt coherence, packaged
resources, direction construction and controls, fingerprint statistics,
Transformers and TransformerLens hook adapters, metric/factor identities,
readiness rejection, sealed mock execution/resume, and surface-server resume.

The deterministic mock smoke receipt contains 1,314 intervention/control records,
zero errors, exact zero-hook behavior, and an unchanged record count after resume.
Its readiness score is 9/11 because that intentionally small smoke omits the full
target count and three-point dose grid. Mock output is plumbing evidence only.

## Live MLX backend validation

The SHA-256-pinned receipt at `validation/mlx_gpt2_parity/receipt.json` has status
`validated_mlx_selected` for this one cell:

- `openai-community/gpt2` at revision
  `607a30d783dfa663caf39e06633721c8d4cfcd7e`;
- FP32 `resid_post`, intervention layers 2, 4, 7, and 9;
- four sealed prompt-length cases; and
- Transformers/MPS as the reference and MLX Metal as the candidate.

All **80/80 parity gates passed**, including exact token IDs, baseline and changed
logits/activations, zero-hook no-op, argmax agreement, intervention fidelity, and
delta direction and magnitude. On the recorded synchronized end-to-end benchmark,
aggregate medians were 17.517 ms for Transformers/MPS and 10.727 ms for MLX, a
**1.633× speedup**. The receipt SHA-256 is:

```text
98c3873a1ec6166aeae0fbb5d9abcd587eb1b3996726912ab963ff35ee497679
```

Absolute latency reflects runtime load; the sealed comparison passed its relative
speed gate. This is a backend-selection result on one machine and workload, not a
general MLX speed claim or evidence about glyphs. Other models, revisions, dtypes,
sites, hardware, prompt distributions, and quantized variants remain unvalidated.

## Standard MLX matrix

The completed matrix bound to the pinned parity receipt and current source is:

```text
colored-shapes-v1-standard-mlx--mlx--openai-community-gpt2--c493ae1e18743922
```

It completed in 254.633 seconds with 14,208 intervention/control records, zero
errors, 11/11 pre-causal readiness checks, exact zero-hook activation and logit RMS
deltas of 0, and `causal_claim_authorized: false`. Its artifact audit passed
15/15 checks with status `ready_with_caveats`:

```text
validation/run_audits/colored-shapes-v1-standard-mlx--c493ae1e18743922.json
```

The hardened seal binds configuration and data hashes, the pinned parity receipt,
installed source, dependency/runtime identity, and the loaded model's
path-independent artifact manifest. Backend load occurs before run-directory
selection, so runtime or model-manifest changes create another run ID rather than
silently resuming old records under a rewritten receipt.

## Required interpretation limits

- The full 14,208-record pipeline has been run on MLX only. PyTorch/MPS parity
  covers fixed prompts, layers, and vectors; it is not a duplicate full-matrix run.
- Fingerprint advantage is heterogeneous across cells, including non-positive
  cells. Report the distribution, median, and cross-seed aggregate; do not select
  only the maximum row.
- Primary glyph token counts are balanced, but token identities are not. The
  neutral glyph is one token while primary glyphs are three tokens.
- Permutation p-values are screening flags at a finite `1/1001` floor and are not
  multiplicity-corrected global significance tests.
- Source seeds are repeated direction estimates, not independent observations;
  target prompts are the principal sampling clusters.
- Iso-KL, SAE, generation, `resid_pre`, `attn_out`, `mlp_out`, and path-level
  causal tests were not run.

The completed result is a reproducible pre-causal fingerprint candidate and a
basis for targeted follow-up. It does not identify glyph meaning, a circuit, or a
causal path.
