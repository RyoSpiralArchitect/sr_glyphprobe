# T13-EA emoji-steering specificity 点推定証跡

[English](README.md) · [点推定結果](../../docs/EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.ja.md) · [凍結済み解析計画](../../docs/EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0.ja.md) · [ゼロゲート修正](../../docs/EMOJI_STEERING_SPECIFICITY_ZERO_GATE_AMENDMENT_V1.ja.md)

状態: **探索的な点推定証跡は完了。注意事項を添えれば共有可能。登録済みbootstrapは
0 / 20,000回のまま**。

このdirectoryには、T13-EAの公開用証跡を軽量な形で収めている。主な結果は、
構造を持つ一方でemojiに固有とは言えない介入幾何である。Source formの効果はdepth、
dose、target、model、glyph systemに依存する。一般的なtarget susceptibility、wrapper依存、
正方向isotropicだけのnullも、代替説明として残る。意味、機構、行動、確認的な結論は導かない。

## 収録した証跡

- `reporting_summary_v0.json`：F1〜F6の全点推定出力から、報告用に決定論的に作った
  summary。結果文書の主要数値を再計算できるよう、全endpointと体系的な集約を、
  weight・denominatorとともに残す。
- `PUBLIC_MANIFEST.json`：収録summary、省略した6つのsource output、furnace側archive、
  claim boundaryの一覧。
- `SHA256SUMS`：公開bundle 4 fileのSHA-256。
- 生成に使う
  [`summarize_emoji_steering_specificity_analysis_v0_results.py`](../../scripts/summarize_emoji_steering_specificity_analysis_v0_results.py)
  は、凍結済みIDとstatus、productionの正確row数、有限値、amendmentとcloseoutのbinding、
  source fileのbyte数とSHA-256を先にfail-closedで検査する。Model inference、bootstrap、
  significance test、outcomeに基づく除外は行わない。

Summaryは1,127,906 byte、SHA-256は
`097934b191660106167164e2f60f18edafc7fe148db55760466b525aa74c6d06`。別の出力先でも
byte単位で一致した。

## 省略した証跡

検証済みsource output 6件は合計104,583,753 byteで、Gitには収録しない。個別のbyte数と
hashはpublic manifestとsummaryの両方に残す。Furnace側のacquisition archiveは、検証済み
1,161 file、4,535,141,572 byteである。Raw arrayはGitにもSpiralShareにも複製していない。

Hashは検収したdataとの同一性を固定するが、省略fileを復元できない。このbundleからは、
認証済み派生出力を元に報告した集約点推定値を再現できる。Raw activationから派生出力自体を
独立に再構築することはできない。

## ゼロゲートの履歴

当初のexact-JS gateは、非ゼロの科学値を開く前にfail-closedし、解析出力も書かなかった。
その失敗は保存している。別の数値修正は、live residualの正確な大きさを見る前に凍結した。
修正後もprimitive no-opは厳密なままで、float32から派生するJS round-tripだけに、
固定済みの`8 * eps(float32)`を使う。このgate通過は科学的な証拠ではなく、exact JSも主張しない。

## 再現方法

省略した6つのsource outputの認証済みcopyがある場合は、次のように生成できる。

```bash
python3 scripts/summarize_emoji_steering_specificity_analysis_v0_results.py \
  --outcomes-point-json /path/to/outcomes-v1-point.json \
  --geometry-directory /path/to/geometry-v1 \
  --point-results-closeout-json \
    validation/emoji_steering_specificity_analysis_v0/point_results_closeout_979533f.json \
  --output-json /path/to/new-reporting-summary.json
```

Output pathは、実行前に存在してはならない。macOS上でpublic bundleを検証するには、次を使う。

```bash
cd artifacts/emoji_steering_specificity_analysis_v0
shasum -a 256 -c SHA256SUMS
```

## 凍結した境界

区間推定はまだ収録していない。登録済み20,000 replicateのcluster bootstrapは未実行で、
現在のone-shot analyzerも、決定論的な高位のchunk-and-merge contractとして未凍結である。
それまで論文のinterval gateは閉じたままにする。Exact token ID・prefix対照、wrapper holdout、
正負のmatched null、未使用target bank、残るmodelの介入応答の再現、generation endpointも未実行である。
