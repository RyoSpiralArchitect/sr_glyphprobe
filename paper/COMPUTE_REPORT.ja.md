# Compute report

[English](COMPUTE_REPORT.md)

状態: **T19/T20/T21のcompactな計数は完了。T19のacquisition時間・memoryの計数は未完了**。
model weightのtraining/fine-tuningは行っていない。T20-Cはサイトごとに
3072×8の部分空間パラメータのみを訓練した。

## 記録された実行環境

| 項目 | 記録値 |
|---|---|
| Worker | CUDA対応Linux worker 1台 |
| GPU | NVIDIA GeForce RTX 5090 |
| Backend | Transformers / CUDA |
| Activation・model compute dtype | model実行はBF16、保存activation arrayは`float32` |
| PyTorch | `2.13.0+cu132` |
| Transformers | `5.15.0` |
| NumPy | `2.5.2` |
| PyYAML | `6.0.3` |
| Remote code | 無効（`trust_remote_code: false`） |
| Model cache | local-only、pinned artifact 9件 |

正確なmodel identifier、40文字revision、想定layer数・width・parameter数は
`configs/semantic_atlas_cross_model_replication_v0.yaml`にある。Llama mirrorの
identifierは実行backendを示さず、凍結safetensorsはTransformers/CUDAで読んだ。

## T19作業量

| Stage | Model作業 | 統計作業 | receiptが立証すること |
|---|---:|---:|---|
| T19-L観測acquisition | batch-one model forward 7,920回、readout vector 285,120件、sealed shard 45件 | acquisition中はなし | 独立validatorがcountとshapeを完全再構成した。 |
| T19-L analysis | model forward 0、intervention 0 | 登録componentごとにrandomization 19,999 draw、item bootstrap 20,000 replicate | compact analysis elapsed timeは6.7235秒。acquisition時間ではない。 |
| T19-C source構築 | model forward 256回 | 6 siteでrank-8 QR/SVD構築 | source/evaluation bankは非重複で、source作業時点ではevaluation intervention未実施。 |
| T19-C evaluation | model forward 2,880回、intervention row 8,064件 | 12 component testの各々でsign flip 99,999回、item bootstrap 20,000 replicate | 独立validatorが6 engineering gateと12統計再構成を全てpassした。 |
| T19-C post-hoc天井（記述的） | model forward 2,304回、intervention row 2,304件 | なし | 登録済み判定の後に計算。post-hoc明記。記録済みoutcomeを変更できない。 |
| T20-C training | capture forward 384回、batched training pass 33,048回（勾配はrank-8部分空間パラメータのみに到達）、記録stage時間14.7分 | source保留32項目でのvalidation scoring | source bankのforwardのみ。admission時のevaluation forward 0を再検証済み。 |
| T20-C evaluation | model forward 32,256回、intervention row 124,416件、記録stage時間7.3分 | 18 component testの各々でsign flip 99,999回、item bootstrap 20,000 replicate | 9 engineering gate全てが厳密ゼロ。独立validatorが全値と両registered verdictを再導出した。 |

T19/T20のforward数は指定したbatch-size-one protocol下のcall数であり、FLOPsではない。因果の
intervention rowは追加training exampleではない。generation callは0件である。

## T21の取得作業量

| 段階 | 対象項目 | バッチforward | 系列換算forward | 記録した所要時間 |
| --- | ---: | ---: | ---: | ---: |
| 元の使用済み項目canary | 8 | 850 | 3,634 | 19.48秒 |
| 使用済み項目による探索 | 384 | 4,610 | 138,242 | 218.87秒 |
| 確認実行処理のcanary、同じ使用済み項目 | 8 | 850 | 3,634 | 19.73秒 |
| 事前指定した確認実験 | 195 | 2,720 | 70,580 | 118.50秒 |

ドナーの取得と標準attentionとの一致検査も含む。介入forwardは文脈ごとに88行で、
同じバッチ位置の対照forwardと対にする。canaryは既存項目の繰り返しであり、科学的な
標本数を増やさない。新モデルの取得、モデル重みの訓練、生成はいずれも行っていない。
所要時間には読み込み・取得・保存も含み、GPUの計算時間だけではない。T21の最大メモリ
使用量とエネルギー消費は未計測である。

確認実験の主要推定は、インデックスを共有する項目bootstrap 20,000回を用いる。
別実装でも保存状態から区間を再計算した。匿名資料には195項目の比較値とNumPyだけで
動く統計検証コードを同梱する。生のモデル状態からの再構成には、別途保管している配列が
必要である。

## 査読後のCPU検証

2026-09-02の査読対応では、同じLinux側のNumPy 2.5.2で保存済み出力だけを用いた。
T21の再構成はBLAS/OpenMPを4 thread、T19の再計算は2 threadに制限した。
T21の13 chunkと10指標配列を再構成して195項目のマージン成分を出力し、T19の全36
randomization検定・36 bootstrap区間、T20の27訓練履歴・9採用時点を再計算した。
追加のモデル実行・生成・成分の有意差検定はいずれも0で、GPU計算は要求していない。
段階別のCPU時間・最大メモリを別途計測していないため、速度倍率や総計算量は主張しない。

T19のコンパクトな予測、T20の採用検証、T21の記述的分解はarchive v3に含める。
raw状態は引き続き省略する。

## 既知の欠落

compact T19 receiptには、acquisition wall-clock、peak CUDA memory、CPU model、system
RAM、raw scratch storage、energy useが保存されていない。また、T19を動機づけた
探索的T9--T18の総computeも集計していない。過去のT10 engineering receiptには
model別timing・peak memoryの一部があるが、input/readout workloadが異なるため、
T19の値へ代用すると根拠のない推定になる。

したがってNeurIPS compute-resources checklistは**No**を維持する。このreportは
利用できる正確な事実だけを示し、事後的にduration/memoryを推定せず、最小の欠落証拠を
明示する。
