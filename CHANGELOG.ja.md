# 変更履歴

[English](CHANGELOG.md)

## 未リリース — MLX 高速化と provenance 強化

- Apple silicon 向け MLX-LM バックエンドを追加し、全シーケンスの `resid_post` capture と activation 介入に対応。
- 未対応の MLX site、attention output、generation、安全性を確認できない custom model 引数、量子化 model の明示的 dtype 変換を fail-closed に変更。
- MLX activation patch capability を、SHA-256 で固定した同一 model receipt で gate。status、revision、dtype、site、現行実装、stable model identity、parity check、speed gate の一致を必須化。
- receipt が検証した intervention layer を runtime で強制し、capture-only call と private parity probe は明示的に分離。
- token、activation、logit、zero-hook、介入方向、介入 magnitude、同期 end-to-end 速度を確認する、固定 GPT-2 FP32 parity validator を追加。
- path 非依存の model-artifact manifest を追加し、run directory の選択を backend load 後に変更。
- run seal に dependency/runtime と stable loaded-model identity を追加し、runtime または model manifest を跨いだ resume を防止。
- MLX validation receipt を config file からの相対 path として解決し、panel、wrapper、target input と同じ path semantics に統一。
- `configs/v1_mlx_standard.yaml`、packaged starter resource、MLX optional dependency group、complete-run artifact validator を追加。
- 欠測値または非有限値がある readiness check を fail-closed にし、表示する criterion と実際の判定条件を一致。
- 収録/省略 file の hash、POSIX/Windows 絶対 path の公開防止、copy 前の run/audit/parity 相互照合を備えた、fail-closed な compact public-bundle builder を追加。
- artifact audit が失敗した場合、status/decision と一貫して `scientific_result: false` になるよう修正。
- 標準 MLX 行列を検証: 14,208 record、0 error、11/11 readiness、別立の 15/15 artifact audit と明示的 caveat。
- test suite を 76 passing tests に拡張。
- 公開ドキュメントの英日ペア管理と、再現可能で反証可能な英語論文を Phase I の目標とする方針を導入。

## 0.1.0

固定済み事前因果 harness の初期版。

- バランスされた 10 glyph の color × shape panel を追加。
- raw Transformers、TransformerLens、決定論的 mock バックエンドを追加。
- vLLM、llama.cpp、Ollama、LM Studio、generic endpoint 向けの OpenAI-compatible adapter を追加。
- 明示的な capability receipt と surface-only fallback boundary を追加。
- wrapper-resampled direction replicate、panel centering、generic-emoji separation、RMS strength matching、global RMS clipping、sign flip、panel span に直交する random control を追加。
- distribution、activation、geometry、factor、fingerprint、latency、tokenization、任意 SAELens measurement を追加。
- 反復 group-stratified split-half、target 内 label permutation、cross-seed fingerprint、scalar-balance table、dose response、sign-flip symmetry、明示的 zero-hook diagnostic を追加。
- 決定論的 task ID、resume 可能な JSONL run、input hash、planning、backend/model matrix、Markdown report を追加。
- `resid_pre`、`attn_out`、`mlp_out`、`resid_post` の標準 component-site matrix と、wrapper ごとの正確な tokenization receipt を追加。
- `glyphprobe init` による packaged starter resource を追加し、install された Python source-tree hash を各 run ID に seal。
