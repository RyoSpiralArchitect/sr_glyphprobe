# Asset and license audit

[日本語](ASSET_LICENSES.ja.md)

Status: **reviewed for the anonymous T19/T20/T21 submission artifact on 2026-09-02**.
T21 reuses the same Llama checkpoint and Unicode/CLDR sources; it introduces
derived scalar contrasts and project code, with no new upstream model assets.
Since archive v3, the package also includes derived T19 prediction indices, T20 selection
diagnostics, and T21 margin components; it adds no upstream model files.
This register distinguishes permission to use an upstream asset from permission
to redistribute the asset itself. The anonymous archive contains no model
weights or tokenizer files.

## Model checkpoints

| Frozen artifact(s) | Terms declared by the pinned model card | Archive treatment |
|---|---|---|
| `Qwen/Qwen2.5-0.5B`, `Qwen/Qwen2.5-1.5B`, `Qwen/Qwen2.5-7B` | Apache License 2.0 | Identifier and pinned revision only; no weights or tokenizer files. |
| `Qwen/Qwen2.5-3B` | Qwen Research License Agreement, non-commercial research or evaluation use | Used only for this non-commercial research study; identifier and pinned revision only; no Qwen Materials are redistributed. |
| `allenai/OLMo-2-0425-1B` | Apache License 2.0 | Identifier and pinned revision only; no weights or tokenizer files. |
| `HuggingFaceTB/SmolLM2-1.7B` | Apache License 2.0 | Identifier and pinned revision only; no weights or tokenizer files. |
| `google/gemma-2-2b-it` | Gemma Terms of Use | Identifier and pinned revision only; gated files are not redistributed. |
| `mlx-community/Llama-3.2-3B-bf16` | Llama 3.2 Community License | Identifier and pinned mirror revision only; no weights, tokenizer files, or upstream license grant are redistributed or sublicensed. The run used the mirror's safetensors through Transformers/CUDA, not MLX. |
| `mistralai/Mistral-7B-Instruct-v0.3` | Apache License 2.0 | Identifier and pinned revision only; no weights or tokenizer files. |

Primary records: [Qwen 0.5B](https://huggingface.co/Qwen/Qwen2.5-0.5B),
[Qwen 1.5B](https://huggingface.co/Qwen/Qwen2.5-1.5B),
[Qwen 3B and its research license](https://huggingface.co/Qwen/Qwen2.5-3B/blob/main/LICENSE),
[Qwen 7B](https://huggingface.co/Qwen/Qwen2.5-7B),
[OLMo 2 1B](https://huggingface.co/allenai/OLMo-2-0425-1B),
[SmolLM2 1.7B](https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B),
[Gemma 2 2B IT](https://huggingface.co/google/gemma-2-2b-it),
[Llama 3.2 3B mirror](https://huggingface.co/mlx-community/Llama-3.2-3B-bf16), and
[Mistral 7B Instruct v0.3](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3).
The full 40-character revisions are frozen in
`configs/semantic_atlas_cross_model_replication_v0.yaml`.

## Unicode and CLDR data

The selection manifest contains derived labels and metadata from Unicode 17.0
and CLDR 48.2. These data are used under the **Unicode License v3**. The
required copyright and permission notice is reproduced in
[`UNICODE_LICENSE.txt`](UNICODE_LICENSE.txt) and is shipped beside every copy
of the derived manifest in the anonymous archive. The exact source URLs,
versions, byte counts, and SHA-256 values are frozen in
`configs/t19_lexical_alias_unicode_control_v0.yaml`.

The archive does not include the upstream Unicode or CLDR source files. It
includes only the frozen selected rows needed to identify the experimental
banks. No trademark permission is claimed.

## Code, libraries, and paper template

- New project code and documentation are distributed under Apache License 2.0;
  the archive includes the complete `LICENSE` text.
- The acquisition stack records PyTorch (`BSD-3-Clause`), Transformers
  (`Apache-2.0`), NumPy (`BSD-3-Clause`), and PyYAML (`MIT`) versions. Figure
  regeneration additionally uses Matplotlib (`PSF-based` license). Their
  packages are not vendored in the archive.
- The manuscript uses the official NeurIPS 2026 formatting archive. Its source
  URL and SHA-256 are recorded in `paper/README.md`. The anonymous evidence
  archive omits the conference style and template files rather than asserting
  a separate redistribution license; reviewers can obtain the exact official
  archive from the recorded source.

## Audit conclusion

All upstream scientific assets used by T19 have an identified source and
terms. Restricted checkpoint files are referenced rather than redistributed;
the Qwen 3B cell is explicitly bounded to non-commercial research; and the
Unicode permission notice travels with the derived selection manifest. This
register is a provenance and terms-of-use audit, not legal advice and not a
license grant for any upstream asset.
