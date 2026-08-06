# バックエンドの能力境界

[English](BACKENDS.md)

CLI は共通だが、バックエンド名が同じ数値対象を扱うことを保証するわけではない。
実行結果を比較する前に、`capabilities.json`、`receipt.json`、および以下の各セクションを
確認する。

## 内部バックエンド

### TransformerLens (`lens`)

`lens` は標準的なフック経路である。TransformerLens のフック名を使い、
`TransformerBridge.boot_transformers` を優先し、バージョン互換の
`HookedTransformer.from_pretrained` をフォールバックとする。ローダ引数、解決済み dtype、
層数、幅、ローダ経路、モデル receipt を記録する。

### Transformers/PyTorch (`transformers`)

`transformers` は `AutoModelForCausalLM` と PyTorch のモジュールフックを使う。デコーダブロックは
保守的に検出する。`resid_post` はデコーダブロックの出力を指す。`resid_pre`、`attn_out`、
`mlp_out` はモデル系列の構造に依存するため、モデル固有のパリティ receipt なしに異なる
アーキテクチャ間で比較しない。選択した公開 dtype 引数名、解決済み dtype、ローダ引数、
ローカルのモデル・アーティファクト manifest を記録する。

### MLX-LM (`mlx`)

`mlx` は Apple silicon 向けの経路である。選択したデコーダブロックを一時的にプロキシ化し、
全シーケンスに対するブロック出力を取得または編集し、遅延計算グラフ全体を評価して NumPy に
コピーする。プロキシの差し替え中は、1 つのバックエンドインスタンスで複数の forward を並行実行しない。

現在の実装が対応するのは `resid_post` の取得と介入だけである。`resid_pre`、`attn_out`、
`mlp_out`、または attention weight の要求は fail-closed で拒否する。生成機能は公開しない。
量子化 MLX モデルでは `dtype: auto` が必要で、研究に使う前に独立したパリティ検証を要する。

forward logits と hidden-state capture は、パリティ receipt がなくても調査できる。一方、activation 介入は
別扱いである。SHA-256 で固定された receipt を読み込み、status、model、revision、dtype、site、
現行のソースツリー hash、安定化したモデル identity、parity gate、speed gate がすべて一致した場合だけ、
activation patch 能力を有効とし、介入を許可する。receipt が欠落、変更、陳腐化、または検証失敗の状態なら、
activation patch は無効になるか拒否される。

同梱の検証済みセルは、意図的に次の範囲に限定している。

- モデル: `openai-community/gpt2`
- revision: `607a30d783dfa663caf39e06633721c8d4cfcd7e`
- dtype/device: MLX Metal GPU 上の FP32
- site: `resid_post`
- 介入層: 2、4、7、9
- パリティ負荷: 長さの異なる 4 つの固定 prompt、token ID の完全一致、baseline/介入後の
  activation と logits、zero-hook、介入差分の方向と大きさ、同期させた end-to-end latency

この receipt は、他のモデル、revision、dtype、site、hardware、prompt 分布、量子化セルを検証しない。
`model_receipt` には MLX/MLX-LM のバージョン、解決済み device/dtype、block path、量子化情報、
model locator、および解決したモデル・アーティファクトの path 非依存な file manifest を記録する。

### 決定論的 mock (`mock`)

`mock` は CI と end-to-end 配線の確認に使う、決定論的に生成された合成 residual stream である。
モデルに関する証拠にはならない。

## OpenAI 互換サービングバックエンド

`vllm`、`llamacpp`、`ollama`、`lmstudio`、`openai` は共通の生成アダプタを使う。標準的な互換 endpoint は
residual stream や任意の activation patch を公開しないため、これらのバックエンドには
`surface-observational-only` の境界を付与する。

アダプタは top-logprob 対応を実行時に調べる。互換性のための再試行では、logprobs を残す引数の組み合わせを
優先しつつ、非対応フィールドを取り除く。resume された run では、neutral baseline を再生成せず保存済み情報から
復元する。

## バックエンド間の比較

同じ model identifier だけで同値性は保証されない。tokenizer revision、chat template、fused kernel、量子化、
GGUF 変換、weight processing、device precision はいずれも出力を変え得る。すべての比較を、正確なバックエンド、
モデル・アーティファクト manifest、実装 hash、runtime receipt、明示的なパリティ負荷に結び付ける。
MLX パリティ receipt はバックエンド選択の gate であり、glyph に関する研究結果ではない。
