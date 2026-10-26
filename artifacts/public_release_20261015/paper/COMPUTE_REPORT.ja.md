# Compute report

[English](COMPUTE_REPORT.md)

10月15日の状態: **新しい読み出し実験の取得は完了。過去のT19/T20/T21の計数を保持し、
T19のacquisition時間・memoryの計数は未完了**。
model weightのtraining/fine-tuningは行っていない。T20-Cはサイトごとに
3072×8の部分空間パラメータのみを訓練した。

## 過去に記録された実行環境

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
| T19-C 事後的な全状態の参照交換（記述的） | model forward 2,304回、intervention row 2,304件 | なし | 登録済み判定の後に計算。事後解析と明記。記録済み結果を変更せず、普遍的な上限も立証しない。 |
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

T19のコンパクトな予測、T20の採用検証、T21の記述的分解はarchive v3以降に含める。
raw状態は引き続き省略する。

## 10月10日の作業原稿への追補

文脈実験の実行形状を揃えた再採点は候補文624対（科学的な系列採点1,248件と過去の検査64件、
計1,312 forward）。続く二系統の開発実験は1,632対（系列3,264件と検査32件、計3,296 forward）を
完了した。後者は記録されたRTX 5090で638.744943秒を要し、Torchの最大割当／予約メモリは
6,195.231／6,318 MiBだった。両段階とも同じ24課題・6系列を再利用しており、独立した課題数は
増えていない。Llama 3.2 3B baseをBF16、Transformers/CUDA、eager attentionで実行し、
重みの訓練と自由生成は行っていない。

[作業原稿用の集計](../validation/contextual_emoji_working_revision_20261010/summary.json)で、
これらの数を完了記録と対応づける。10月10日のノート・原稿更新は保存済みデータを手元で再計算し、
モデルforward、tokenizer呼出し、GPU作業を追加しない。執筆とCPUの所要時間は別途計測していない。
文脈研究全体の計算量を集計したものではなく、過去の時間・メモリ・電力・炭素の欠落も埋めない。

## 10月15日の明示報告による読み出し適格性検査

[事前指定した設計](../docs/READOUT_QUALIFICATION_V1.ja.md)では、作成した4系列・32件の
新しいテキスト課題を、開発用16件と保留検査用16件に分ける。報告の3状態、命題の2極性、
質問3形式、回答4形式で候補文2,304対となり、科学的な系列forward 4,608件と過去の検査32件、
計4,640 forwardを予定する。反復条件を独立した2,304課題とは数えない。モデル、実行環境、
全入力のトークン列は[準備済み仕様](../validation/readout_qualification_v1/specification.json)で固定し、
SHA-256は`5273b1f86db4ee956659a94ca7f047856e86b5f857fdf66efc5d96e5f85c487f`。

取得済みの`mlx-community/Llama-3.2-3B-bf16`、revision
`60a99aaf43164077157d64bf909b7b61143c6a6d`を、Transformers/CUDAのBF16、
eager attentionで実行する。ミラー名はMLXで実行したことを意味しない。
モデルの取得、重みの訓練、自由生成、著者の個別記録、保護対象の過去のholdoutは含めない。
過去の検査値と厳密比較するため既存のlogit採点処理を使い、管理された実行環境を変更しない。

上限は1,800秒、Torch割当9,728 MiBとdriver分512 MiBで、他のGPU処理が同時にある場合は実行しない。
forward前後で使用状況を確認し、中断時も予定・完了・欠測の分母を残す。

取得は**4,640/4,640 forward、2,304/2,304対を完了**し、欠測0、所要時間は
**889.365958秒**（約14.82分）だった。Torchの最大割当／予約メモリは
**6,195.228/6,312 MiB**。実行全体の経過時間とallocatorの計測であり、kernelだけの時間、
システム全体の最大メモリ、電力、炭素の推定ではない。モデルのdownload・重み訓練・自由生成は0件で、
競合による停止や自動再試行なしに正常終了した。

[完了記録](../validation/readout_qualification_v1/run4640/run_completed.json)で数値の受入検査を確認する。
[別実装の算術検証](../validation/readout_qualification_v1/independent_validation.json)は保存した値から
予定4,640行と2,304対を再構成し、モデルforwardとtokenizer呼出しを追加しない。
有限集合の二つの適格性判定がともに不合格になることも一致した。数値の検査通過は適格性の通過ではない。
[論文用の集計](generated/readout_qualification_20261015/summary.json)には、分割・形式の全組合せ、
報告状態別の内訳、同点、課題別の集計を残す。CPU検証と執筆の所要時間は別途計測していない。
過去の計算量の欠落も変わらない。

## 既知の欠落

compact T19 receiptには、acquisition wall-clock、peak CUDA memory、CPU model、system
RAM、raw scratch storage、energy useが保存されていない。また、T19を動機づけた
探索的T9--T18の総computeも集計していない。過去のT10 engineering receiptには
model別timing・peak memoryの一部があるが、input/readout workloadが異なるため、
T19の値へ代用すると根拠のない推定になる。

このため、過去のNeurIPS投稿のcompute-resources checklistは**No**だった。
独立プレプリントでは投稿用checklistを外すが、計算量記録の欠落は残る。このreportは
利用できる正確な事実だけを示し、事後的にduration/memoryを推定せず、最小の欠落証拠を明示する。
