# 再現性ガイド

[English](REPRODUCIBILITY.md)

このガイドは、公開した MLX validation と標準的な事前因果行列を再現するためのものである。
異なる hardware で wall-clock time が同じになることは保証しない。

## 1. 環境を準備する

MLX セルには、MLX Metal が利用できる Apple silicon が必要である。package metadata 上の対応 Python は
3.11–3.13 である。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[mlx,torch,dev]'
python -m pytest
```

このガイドのコマンドは、すべて repository checkout の root で実行する。

公開版の test suite は 76 テストである。MLX の研究経路には、これに加えて以下の live モデル/
バックエンド検証が必要である。決定論的な adapter test で代替しない。

## 2. 固定した model revision を準備する

同梱 MLX セルは次を使う。

```text
model: openai-community/gpt2
revision: 607a30d783dfa663caf39e06633721c8d4cfcd7e
dtype: float32
site: resid_post
```

`configs/v1_mlx_standard.yaml` は `local_files_only: true` である。offline 実行の前に、この revision と完全に一致する
Hugging Face snapshot を用意する。バックエンドは、解決した model artifact を path 非依存の file manifest として
hash 化する。model 名や revision 文字列だけでは provenance として不十分である。

## 3. バックエンドの parity/speed gate を再現する

```bash
python scripts/validate_mlx_gpt2_parity.py \
  --output validation/mlx_gpt2_parity/receipt.candidate.json
shasum -a 256 validation/mlx_gpt2_parity/receipt.candidate.json
```

正式な `receipt.json` の SHA-256 は、標準 config の `backend.validation_receipt_sha256` に固定している。candidate は、
timing や receipt metadata が新しくなるため、通常は別の hash になる。candidate 全体を review し、`receipt.json` に昇格させ、
source と packaged resource の両 config にある hash を同じ review 単位で更新する。どちらの receipt も手作業で編集しない。

receipt が通過し、その hash、source-tree identity、stable model identity、model、revision、dtype、site が読み込み済み
バックエンドと一致しない限り、activation patch は無効のままである。speed gate は、固定行列における MLX の総合 median が
Transformers/MPS より少なくとも 5% 速いことを求める。

## 4. 標準行列を inspect/run する

```bash
glyphprobe inspect -c configs/v1_mlx_standard.yaml
glyphprobe plan -c configs/v1_mlx_standard.yaml --load-model
glyphprobe run -c configs/v1_mlx_standard.yaml
```

config 内の path は、validation receipt を含め、config file からの相対位置として解決する。標準セルは panel、wrapper、
target、seed、strength、layer、control、model revision、receipt、receipt hash を固定する。resolved config と plan を run と一緒に保存する。

## 5. Run seal を理解する

バックエンドの load に成功した場合、run ID は次を含む seal から決まる。

- resolved config、panel、wrapper、target
- config、parity receipt、data file の順序付き SHA-256 receipt
- install された GlyphProbe Python source-tree hash
- dependency/runtime environment receipt
- path と load-time noise を除き、path 非依存 model-artifact manifest を含む stable loaded-model identity

run directory の選択前にバックエンドを load するため、resume 時に異なる dependency/runtime や model artifact の既存 record を
再利用しつつ新しい receipt に書き換えることはできない。seal が変われば run ID も変わる。既存 directory の receipt が
現行 seal と一致しない場合、resume を拒否する。

receipt は生成時から、portable な input label、path 非依存の model locator、local directory の代わりの run ID を使う。
この性質を保ち、絶対 local path が見つかった場合は公開を止める。sealed artifact を後からサニタイズせず、emitter を修正して再生成する。

## 6. 完了した run を検証する

```bash
python scripts/validate_standard_run_artifacts.py \
  path/to/run-directory \
  --output validation/run_audits/run-audit.json
```

validator は、input/実装の結び付け、計画/実測 record 数、決定論的 task ID の一意性、必須 field、主要 metric の
有限性、target/tokenization profile、headline summary、readiness を再計算する。fingerprint cell 全体の分布とすべての caveat を残す。
15/15 audit と 11/11 readiness の通過は、より細かな実験への進行を許すが、因果・意味の結論を許可しない。

## 7. 外部公開用のコンパクトな証拠 bundle を作る

```bash
python scripts/build_public_artifact_bundle.py \
  --run-dir path/to/run-directory \
  --parity-receipt validation/mlx_gpt2_parity/receipt.json \
  --audit-receipt validation/run_audits/run-audit.json \
  --output-dir path/to/public-artifacts
```

builder は、local な POSIX/Windows 絶対 path または `file://` URI を含む text artifact の公開を拒否する。コンパクトな summary をコピーし、
収録 file と省略した大容量 ledger/array の hash を含む manifest を生成する。省略対象の hash は local file の存在を結び付けるが、
そのデータを復元可能にするわけではない。論文水準の公開では、完全な sealed run を別途 archive する。

## マシン固有の量

wall-clock latency、load time、peak device memory、dependency/OS version、hardware 固有 kernel、timestamp は receipt に記録する。
local filesystem path は記録しない。異なるマシン間で run ID や benchmark 値を無理に一致させるために、runtime 量を消去しない。
