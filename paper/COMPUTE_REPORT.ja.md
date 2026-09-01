# Compute report

[English](COMPUTE_REPORT.md)

状態: **T19のcompactな計数は完了したが、acquisition時間・memoryの計数は未完了**。
modelのtraining/fine-tuningは行っていない。

## 凍結した実行環境

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

forward数は凍結batch-size-one protocol下のcall数であり、FLOPsではない。因果の
intervention rowは追加training exampleではない。generation callは0件である。

## 既知の欠落

compact T19 receiptには、acquisition wall-clock、peak CUDA memory、CPU model、system
RAM、raw scratch storage、energy useが保存されていない。また、T19を動機づけた
探索的T9--T18の総computeも集計していない。過去のT10 engineering receiptには
model別timing・peak memoryの一部があるが、input/readout workloadが異なるため、
T19の値へ代用すると根拠のない推定になる。

したがってNeurIPS compute-resources checklistは**No**を維持する。このreportは
利用できる正確な事実だけを示し、事後的にduration/memoryを推定せず、最小の欠落証拠を
明示する。
