# T13-EA Bootstrap実行 v1

[English](EMOJI_STEERING_SPECIFICITY_BOOTSTRAP_EXECUTION_V1.md) · [点推定結果](EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.ja.md) · [元の解析契約](EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0.ja.md)

状態: **結果を見た後の計算実装追補を凍結済み。本番bootstrapは未実行**。

登録済みのT13-EA bootstrap 20,000回を、決定論的なchunkとして実行できる形に
落とし込んだ。今回固定したのは、高位estimandの完全なroster、replicateから
抽出列を決める規則、chunk境界、merge順序、完全性receipt、失敗条件である。
凍結時点では本番bundleをまだ作っておらず、完了chunkもない。実行数は
**0 / 20,000**のままである。

## なぜ別の追補にしたか

元のT13-EA契約では、familyごとの再標本化単位、20,000回、seed
`2026082913`、pointwiseな95% percentile区間、全chunkをhash検証してから
mergeするgateまでを事前に固定していた。しかし、区間を付けるmarginalization
rowの完全な列挙と、chunkの実行順に依存しない乱数scheduleは未定義だった。
従来の一括analyzerにも、細かなsurfaceを大量にbootstrapする一方、公開済みの
高位macro rowには揃ったreplicate区間を付けられないという食い違いがあった。

この実装上の空白を閉じた時点で、点推定結果はすでに見えていた。したがって、
この追補は結果を見た後のものだと明記する。600 rowの厳密なrosterが事前登録
されていたとは扱わない。採用規則は一つだけである。公開済みの高位reporting
synthesisに含まれるmodelとendpointのrowを、sign、depth、効果量、向き、
面白さで選別せず、そのまま全件写す。

得られる区間は、完了後も記述的かつ探索的である。Primary hypothesis、有意差判定、
確認、emoji固有の機構、意味解釈、tokenizer非依存性、scale law、model母集団への
一般化を新たに与えるものではない。

## 凍結したestimand roster

機械可読のrosterは
[`configs/emoji_steering_specificity_bootstrap_estimands_v1.json`](../configs/emoji_steering_specificity_bootstrap_estimands_v1.json)
に置いた。Index付きのestimandが、重複なく600本並ぶ。

| Family | Row数 | 区間を付ける高位estimand |
|---|---:|---|
| F1 item source form | 108 | 全model × contrast × sign × endpointのpaired difference平均 |
| F2 prototype depth/dose | 168 | 全model × endpoint × depthのraw macro平均、全model × endpointのdose ordering平均、model別entropy antisymmetry 2指標 |
| F3 random calibration | 324 | 全model × endpoint × depth、および全model × endpointのdepth平均について、random-relative 2指標 |
| **合計** | **600** | 結果に基づく部分集合なし |

F1〜F3の細粒度point tableは、公開済みの点推定解析に全件残る。削除も非表示化も
しない。ただし、結果を見た後に選んだ細胞へ区間を付け足すことはせず、この高位roster
の外側は点推定のまま保持する。

## 再標本化schedule

Replicate IDは`0`から`19999`まで。200回ずつ、連続した100 chunkへ固定した。

- `chunk-0000`: `[0, 200)`
- `chunk-0001`: `[200, 400)`
- …
- `chunk-0099`: `[19800, 20000)`

抽出には、counter方式のSHA-256 samplerとunbiased rejectionを使う。各drawは、
固定seed、namespace、replicate ID、draw index、rejection attemptだけで決まる。
どのchunkを先に回したか、どのprocessが担当したか、何chunkを並列にしたかには
依存しない。

32 targetの抽出列は、F1、F2、F3、全endpoint、3 modelで一つに揃える。F1のitem
抽出列は二つある。Glyph-minus-nameは192 item全体、decompositionを使う二つの
contrastは共通の168 itemを再標本化する。F3ではmodelと正規化depthごとに64個の
random seed indexを引き直し、その列をtarget、magnitude、endpoint、system、
source formのすべてで共有する。

## 固定したpoint function

### F1

Model、contrast、sign、endpointごとに、対応の取れたeligible item × targetの
micro平均を求める。Itemとtargetは独立に復元抽出し、二つのmultiplicityの積を
two-way pigeonhole weightとする。Source formのpairは崩さない。

### F2

Raw depthでは、まずsource formを等重みにし、各formで利用可能なsystemを等重みに
する。Magnitudeとsignも等重みである。Doseは、targetごとに
ordered-nondecreasing indicatorを計算してから、登録済みの全
system-form-depth-sign cellを平均する。Entropy antisymmetryは、登録済みの全
system-form-depth-magnitude cellについて、signed sumとnormalized residualを
平均する。

### F3

Replicateごとに、復元抽出した64 seedのmultisetから厳密なmedianを求め、同じ
multisetに対するmidrankを計算する。Source formは等重み、各form内のeligible
systemも等重み、magnitudeも等重みとする。Model全体のrowでは8 depthも等重みに
する。Negative prototypeにはsign-matched random nullがないため、F3へ追加しない。

## Bundleの境界

一度だけ行う`prepare`は、response ledgerを読む前に、既存のscientific-open
closeout、preflight binding、修正版zero gateを同じprocess内で再検証する。その後、
600 estimandに必要なitem・target単位のscalar populationだけを書き出す。公開済みの
600点推定を絶対誤差`1e-12`以内ですべて再生できなければ、最初のchunkへ進まない。

Bundleにはactivation array、raw logit、model weight、cache、prompt本文、target本文、
protected target bankを入れない。Git worktreeの外へ置く。科学open後にderived bundleや
chunkを運ぶ場合も、完全なfile hashを付ける。Raw activation/logit arrayをGitや
SpiralShareへ置くことは、引き続き禁止する。

## Runtimeをまたぐsentinel

各chunkは、本来の200 replicateに加えて、replicate `0`、`9999`、`19999`も再計算する。
その600次元vector 3本をまとめてhash化する。異なるruntimeで作ったchunkを混ぜられる
のは、全chunkのsentinel hashがbit単位で一致した場合だけである。Macと炉の設定が
似ているというだけでは足りず、実際の数値経路が一致して初めて分散実行を認める。

## Mergeと失敗条件

Mergeが受け入れるのは、`chunk-0000`から`chunk-0099`までのちょうど100 directoryだけ
である。欠落、余分、重複、範囲の重なりが一つでもあれば失敗する。Freeze、実行config、
estimand roster、bundle manifest、各file hash、semantic payload hash、replicate範囲、
有限値、共通sentinel hashをすべて検証する。

区間は`q = 0.025, 0.975`に対し、`h = (n - 1) q`とするlinear percentileで固定した。
途中までのchunkから区間receiptを出すことはない。既存の出力pathも上書きしない。

全検査を通ったmerge receiptは、計算上のpaper interval gateをtrueにできる。ただし、
厳密なrosterを点推定後に固定した事実と、confirmatory gateがfalseのままであることを、
同じreceiptに必ず残す。

## 凍結したcommand

Repository freezeを検査する。

```bash
python3 scripts/audit_emoji_steering_specificity_bootstrap_execution_v1.py audit-freeze
```

炉上のlive pathを確定した後、compact bundleを作る。

```bash
python3 scripts/run_emoji_steering_specificity_bootstrap_v1.py prepare \
  --run-root /absolute/path/to/sealed-t13eh \
  --scientific-open-receipt /absolute/path/to/scientific-open-closeout.json \
  --preflight-directory validation/emoji_steering_specificity_harvest_v0 \
  --output /absolute/path/to/t13ea-bootstrap-v1-bundle
```

割り当てられたchunkを一つ実行する。Schedulerは0〜99を任意の順で配ってよい。

```bash
python3 scripts/run_emoji_steering_specificity_bootstrap_v1.py run-chunk \
  --bundle /absolute/path/to/t13ea-bootstrap-v1-bundle \
  --output-root /absolute/path/to/t13ea-bootstrap-v1-chunks \
  --chunk-id 0
```

100 chunkがすべて揃ってからmergeする。

```bash
python3 scripts/run_emoji_steering_specificity_bootstrap_v1.py merge \
  --bundle /absolute/path/to/t13ea-bootstrap-v1-bundle \
  --chunks-root /absolute/path/to/t13ea-bootstrap-v1-chunks \
  --output /absolute/path/to/t13ea-bootstrap-v1-merge
```

これらは凍結した実行手順であり、本番runが完了した証拠ではない。
