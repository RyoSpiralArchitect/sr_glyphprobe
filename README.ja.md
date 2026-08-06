# GlyphProbe

[English](README.md) · [Milestone 2 結果](docs/MILESTONE2_RESULTS.ja.md) · [基準実験の結果](docs/RESULTS_V1.ja.md) · [ロードマップ](docs/ROADMAP.ja.md) · [Phase I 論文計画](docs/PAPER_OUTLINE.ja.md)

GlyphProbe は、絵文字やグリフから作った活性化方向が、言語モデルの出力に再現可能な「指紋」を残すかを調べる研究用ハーネスです。

最初から「モデルの中で、この絵文字は何を意味するのか」とは問いません。介入量、クリッピング、ソース文、ターゲット文、ランダム方向を固定したうえで、方向ごとの差が繰り返し観測できるかを先に確かめます。

既定のパネルは、5色 × 2形状の10グリフです。

```text
🟤 🟫   🟠 🟧   🟢 🟩   🔵 🟦   🟣 🟪
```

## 現在地

2026年8月6日時点で、次の実験セルを検証しています。

- モデル: `openai-community/gpt2`
- リビジョン: `607a30d783dfa663caf39e06633721c8d4cfcd7e`
- 数値形式: FP32
- 介入点: `resid_post`
- 標準レイヤー: 2 / 4 / 7 / 9
- 実行基盤: Apple silicon 上の MLX

MLX は、同じモデル名だから採用したわけではありません。固定した4種類のプロンプト長 × 4レイヤーで Transformers/MPS と比較し、トークン列、基準ロジット、活性化、ゼロ介入、非ゼロ介入を検査しました。80項目すべてが合格し、記録時のエンドツーエンド中央値は 17.517 ms から 10.727 ms に短縮しました（1.633倍）。この検証が認めるのは、上記セルでのバックエンド同等性と、その実行環境・負荷条件での速度差だけです。

続いて MLX で標準スクリーニングを実行し、14,208件の介入レコードをエラーなしで完了しました。前因果的レディネス検査は11 / 11項目、アーティファクト整合性監査は15 / 15項目が合格しています。なお、この全パイプラインを Transformers/MPS でも重ねて実行したわけではありません。主な集約値は次のとおりです。

| 指標 | 値 |
|---|---:|
| ソース方向の反復一致度（中央値） | 0.9705 |
| 絵文字指紋のランダム方向に対する優位量（中央値） | 0.6075 |
| シードをまたぐ指紋優位量（中央値） | 0.9308 |
| KL用量反応の単調性（中央値） | 1.0000 |
| 符号反転の反対称性（中央値） | 0.9997 |
| ゼロ介入による活性化・ロジット変化 | 0.0 |

ただし、36セルのうち優位量が正だったのは25セルで、11セルは非正でした。集約値が正でも、効果が一様に出たわけではありません。現在の結果は、追試に値する**前因果的な指紋候補**です。絵文字の意味、意味表現、回路、因果経路の証明ではありません。

詳しい結果と留保は [実験結果](docs/RESULTS_V1.ja.md)、次の研究段階は [ロードマップ](docs/ROADMAP.ja.md) を参照してください。

### Milestone 2 の現在地

事前検査を通過した後、凍結済み48件のP2バンクを一度だけ開いた。v1の結果は、レイヤーによって分かれている。

| ソースラッパー | レイヤー | 調整済み効果 | 95% CI | Holm補正済みp値 | v1判定 |
|---|---:|---:|:---:|---:|---|
| 主要ソース | 2 | +0.208363 | [0.137463, 0.276893] | 0.00143999 | 指定済みmatched controlsに対して頑健 |
| 主要ソース | 4 | -0.0329465 | [-0.0761085, 0.0110094] | 0.999500 | 未解決 |
| 独立ソース | 2 | +0.187507 | [0.125489, 0.247659] | 0.00393996 | 指定済みmatched controlsに対して頑健 |
| 独立ソース | 4 | -0.086379 | [-0.159246, -0.016917] | 0.999430 | 未解決 |

3つの対照パネルで揃えたのは、3トークンという長さと、パネル単位の9対1の接頭構造である。token IDそのものは同じではない。Panel Cには、事前申告した意味的に近い対照`🟥`を1個含む。独立ソース条件は同じP2ターゲットを再利用しており、独立ターゲットや別モデルでの再現ではない。

別に行ったinput-binding auditは合格した。一方、target bootstrapの各replicateでleave-one-group-out prototypeを作り直す事後感度分析では、区間が広がった。この事後解析は、凍結済みv1判定を上書きしない。その後、2つの二次診断はいずれも14,208行のgridを完走し、errorは0件、zero-hook RMSは0、readinessは11 / 11だった。Random-adjustedのheadline優位量は、末尾token一致で+0.751225、接頭構造均一化で+0.601038である。これはpaired診断で使うraw separation scoreとは別の評価量である。96次元における記述的なstandard-minus-diagnostic中央値は、末尾token一致が+0.002624（36セル中20セルが正）、接頭構造均一化が+0.022096（36セル中25セルが正）だった。これらの事後診断は、推論や同等性の検定ではない。C1因果ホールドアウトは未使用のままである。

実行時の来歴として、matched-null Aの最初のprocessは、マシン負荷が極端に高い最中、798行で外部から中断された。Sealを保ったresumeによって、重複・欠損・error・非ゼロのzero-hook RMSなしで14,208行の正確なgridを完了した。この事象は、モデルに関する証拠でも、一般化できる速度の主張でもない。

正確な結果、解析上の留保、感度区間、エビデンスへのリンクは [Milestone 2 結果](docs/MILESTONE2_RESULTS.ja.md) にまとめた。この結果は前因果段階にあり、意味、機構、回路、因果経路、トークン化から独立したglyph効果を確立しない。

## インストール

Python 3.11 以降を使います。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Apple silicon の MLX 経路を使う場合:

```bash
pip install -e '.[mlx,torch,dev]'
```

TransformerLens、SAELens、ローカル推論サーバー向けの依存関係は [英語版README](README.md) にまとまっています。

## まず動かす

モデルをダウンロードせず、決定論的な模擬バックエンドで一周できます。

```bash
glyphprobe init ./glyphprobe-experiment
cd glyphprobe-experiment
glyphprobe plan -c configs/v1_smoke.yaml --num-layers 8
glyphprobe run  -c configs/v1_smoke.yaml
```

模擬バックエンドは配線検査専用です。そこで得た数値を研究結果には使いません。

## MLX の標準セルを再現する

標準設定には、合格済みレシートのSHA-256があらかじめ固定されています。まずは、そのレシートを使ってパネルと計画を確認し、標準実験を実行します。

```bash
glyphprobe inspect -c configs/v1_mlx_standard.yaml
glyphprobe plan -c configs/v1_mlx_standard.yaml --load-model
glyphprobe run -c configs/v1_mlx_standard.yaml
```

backend実装やモデルセルを変えて再検証するときは、starter workspace から repository checkout の root へ戻り、固定済みレシートを上書きせず候補ファイルへ出力します。

```bash
cd ..  # repository checkout root
python scripts/validate_mlx_gpt2_parity.py \
  --output validation/mlx_gpt2_parity/receipt.candidate.json
shasum -a 256 validation/mlx_gpt2_parity/receipt.candidate.json
```

候補が合格したら、固定レシートと2つの標準configにある `validation_receipt_sha256` を、同じレビュー単位で更新します。速度サンプルは毎回新しく記録されるため、全ゲートが合格してもSHA-256は変わります。

モデル、リビジョン、dtype、量子化、介入点を変えた場合は別の実験セルです。新しい一致検証なしに、今回のレシートを流用しないでください。

## 読み方の約束

- 主な観測単位はターゲットプロンプトです。3つのシードはソース方向の反復推定であり、独立した観測個体ではありません。
- 一次グリフはすべて3トークンですが、トークンIDは同一ではありません。`blue_circle` は中間トークンの接頭パターンが異なり、中立グリフ `·` は1トークンです。
- ラベル置換は36 / 36セルが `p = 1/1001` に達しましたが、これは1,000回置換で到達できる有限の下限です。多重比較を補正した全体有意性ではありません。
- iso-KL、SAE、生成評価、`resid_pre`、`attn_out`、`mlp_out`、パスパッチングは、今回の標準実験では未実施です。
- 公開リポジトリには、再確認しやすい要約、監査結果、ハッシュ付きマニフェストを収録します。約74 MiB（77.3 MB）の生の介入台帳とNPZは含めません。ローカルで再実行すれば生成されます。

## 文書

- [科学的な契約](docs/SCIENTIFIC_CONTRACT.ja.md) / [English](docs/SCIENTIFIC_CONTRACT.md)
- [バックエンド境界](docs/BACKENDS.ja.md) / [English](docs/BACKENDS.md)
- [指標の定義](docs/METRICS.ja.md) / [English](docs/METRICS.md)
- [v1 実験結果](docs/RESULTS_V1.ja.md) / [English](docs/RESULTS_V1.md)
- [Milestone 2 結果](docs/MILESTONE2_RESULTS.ja.md) / [English](docs/MILESTONE2_RESULTS.md)
- [Milestone 2 確認実験プロトコル](docs/MILESTONE2_PROTOCOL.ja.md) / [English](docs/MILESTONE2_PROTOCOL.md)
- [研究ロードマップ](docs/ROADMAP.ja.md) / [English](docs/ROADMAP.md)
- [英語論文の構成案](docs/PAPER_OUTLINE.ja.md) / [English](docs/PAPER_OUTLINE.md)
- [公開研究ノート](docs/NOTE.ja.md) / [English](docs/NOTE.md)

公開向けの手書き文書は、原則として英語版と日本語版を対にします。ライセンス、引用情報、スキーマ、機械生成レシート、コード内コメントは対象外です。

## Phase I のゴール

Phase I の最終成果は、検証可能なアーティファクトを伴う**英語論文または英語プレプリント**です。運用上のMilestone 2は完了し、layer 2は、未使用のC1を使う新しい対象限定型の因果プロトコルを設計できる段階に入りました。Layer 4は未解決のままで、候補にはしません。C1を開く前に、候補、介入、endpoint、対照、多重性familyを凍結します。最終的な論文表現と、それを支える再現実験では、analyzerのrole bindingとprototype再標本化依存に事前に対処します。因果検証、独立backendまたはmodelでの再現、完全な証拠archiveも論文ゲートとして残っています。

## ライセンスと引用

ライセンスは [LICENSE](LICENSE)、引用情報は [CITATION.cff](CITATION.cff) を参照してください。
