# Asset・license監査

[English](ASSET_LICENSES.md)

状態: **2026-09-02にT19/T20/T21匿名投稿artifact向けの確認を実施済み**。
T21は同じLlamaチェックポイントとUnicode/CLDR原資料を再利用し、新たなupstreamモデルは
導入していない。追加するのは派生した比較値とプロジェクトのコードである。この台帳では、
upstream assetを利用する権限と、そのasset自体を再配布する権限を分ける。匿名archiveに
model weightやtokenizer fileは含めない。
Archive v3以降には派生したT19予測index、T20の採用診断、T21のマージン成分も含める。
upstreamのモデルファイルは追加しない。

## Model checkpoint

| 凍結artifact | pinned model cardが示すterms | archiveでの扱い |
|---|---|---|
| `Qwen/Qwen2.5-0.5B`, `Qwen/Qwen2.5-1.5B`, `Qwen/Qwen2.5-7B` | Apache License 2.0 | identifierとpinned revisionのみ。weight/tokenizerは非同梱。 |
| `Qwen/Qwen2.5-3B` | Qwen Research License Agreement（非商用の研究・評価利用） | 本非商用研究だけで使用。identifierとpinned revisionのみで、Qwen Materialsは再配布しない。 |
| `allenai/OLMo-2-0425-1B` | Apache License 2.0 | identifierとpinned revisionのみ。weight/tokenizerは非同梱。 |
| `HuggingFaceTB/SmolLM2-1.7B` | Apache License 2.0 | identifierとpinned revisionのみ。weight/tokenizerは非同梱。 |
| `google/gemma-2-2b-it` | Gemma Terms of Use | identifierとpinned revisionのみ。gated fileは再配布しない。 |
| `mlx-community/Llama-3.2-3B-bf16` | Llama 3.2 Community License | identifierとmirrorのpinned revisionのみ。weight、tokenizer、upstreamのlicense grantを再配布・sublicenseしない。実験ではmirrorのsafetensorsをMLXではなくTransformers/CUDAで読んだ。 |
| `mistralai/Mistral-7B-Instruct-v0.3` | Apache License 2.0 | identifierとpinned revisionのみ。weight/tokenizerは非同梱。 |

一次記録は、[Qwen 0.5B](https://huggingface.co/Qwen/Qwen2.5-0.5B)、
[Qwen 1.5B](https://huggingface.co/Qwen/Qwen2.5-1.5B)、
[Qwen 3Bとresearch license](https://huggingface.co/Qwen/Qwen2.5-3B/blob/main/LICENSE)、
[Qwen 7B](https://huggingface.co/Qwen/Qwen2.5-7B)、
[OLMo 2 1B](https://huggingface.co/allenai/OLMo-2-0425-1B)、
[SmolLM2 1.7B](https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B)、
[Gemma 2 2B IT](https://huggingface.co/google/gemma-2-2b-it)、
[Llama 3.2 3B mirror](https://huggingface.co/mlx-community/Llama-3.2-3B-bf16)、
[Mistral 7B Instruct v0.3](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3)である。
完全な40文字revisionは`configs/semantic_atlas_cross_model_replication_v0.yaml`に
凍結している。

## Unicode・CLDR data

selection manifestにはUnicode 17.0とCLDR 48.2から派生したlabel/metadataを含む。
これらは**Unicode License v3**の下で利用する。必要なcopyright・permission noticeは
[`UNICODE_LICENSE.txt`](UNICODE_LICENSE.txt)へ収録し、派生manifestを含む匿名archiveの
全copyに同梱する。正確なsource URL、version、byte count、SHA-256は
`configs/t19_lexical_alias_unicode_control_v0.yaml`に凍結した。

archiveはupstreamのUnicode/CLDR source fileを収録せず、実験bankを特定するための
凍結済み選択行だけを含む。商標使用権は主張しない。

## Code・library・paper template

- 新規project codeとdocumentationはApache License 2.0で配布し、archiveに完全な
  `LICENSE`本文を含める。
- acquisition stackはPyTorch（`BSD-3-Clause`）、Transformers（`Apache-2.0`）、
  NumPy（`BSD-3-Clause`）、PyYAML（`MIT`）のversionを記録する。figure再生成には
  Matplotlib（`PSF-based` license）も使う。これらのpackageはarchiveへvendorしない。
- 原稿はNeurIPS 2026公式formatting archiveを使う。source URLとSHA-256は
  `paper/README.md`に記録した。conference style/templateに独自の再配布licenseがあると
  主張せず、匿名evidence archiveからは除外する。査読者は記録済みsourceから同一の
  公式archiveを取得できる。

## 監査結論

T19で使った全scientific upstream assetについてsourceとtermsを特定した。制限付き
checkpoint fileは参照だけに留め、Qwen 3B cellは非商用研究へ明示的に限定し、Unicode
permission noticeを派生selection manifestと一緒に運ぶ。この台帳はprovenanceと
terms-of-useの監査であり、法的助言でもupstream assetへのlicense grantでもない。
