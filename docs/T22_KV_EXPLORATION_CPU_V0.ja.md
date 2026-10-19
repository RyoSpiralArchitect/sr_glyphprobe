# T22：露出済み384項目のCPU K/V探索の固定設計

[English](T22_KV_EXPLORATION_CPU_V0.md) | [第2論文の考察](PAPER2_DISCUSSION_NOTES_V0.ja.md) | [8項目の結果](T22_CPU_LEXICAL_RESULTS_V0.ja.md)

状態：**設計・入力を凍結。実行は未承認、384項目の取得は未実施**、2026-10-20 JST。
この設計を書く時点で、最初の8項目のT22結果は既知だった。
新しい384項目の取得に対してprospectiveだが、盲検設計や事前登録された確認実験とは
主張しない。候補・operation・donor・gallery・target panelは、この結果より前の
[判断メモ](T22_KV_DISSECTION_FIRST_STEP_V0.ja.md)で選んでいた。

## 母集団と維持する問い

元のT20/T21 pilotで評価済みの384項目を、元の順序ですべて保持する。
2-token glyphが68項目、3-tokenが316項目。128の元source項目
（2-tokenが22、3-tokenが106）、各targetの元のtoken数一致2 donor、
元のalias-token列も維持する。過去のT22の8項目はindex 0–7で、384項目の要約に
含める。結果が既知・不都合という理由で除外しない。この384項目は露出済みであり、
新たな確認母集団ではない。過去のp2/c1 v1 bankや旧割当scannerを使わない。

問いは、K-only・V-only・joint KV置換が条件付き語彙readoutにどう作用し、
対比が加算的かどうかである。block-21の同じ項目のcodepoint残差reset、
介入blocks 22–27、distance 8、pipe/article-a carrier、glyph/同数suffix位置を保つ。
donor tensorを代入するのはreadout queryのみ。Keyはpost-RoPE、valueは回転していない
value tensorを使う。Vの局所attention weightsは各layer自身の入力で一致する必要が
あるが、後段のquery/attentionは変わりうる。

各carrierでは元の16 extension行をoperation → 位置 → donorの順序で使う：
`none, k, v, kv` × `glyph, suffix` × donor slot `0, 1`。
activeとneutralのbatch形状・行slotは同じ。neutralはresetを維持してdonor置換を無効にする。
glyphのtoken数がどちらでもこのbatch形状を維持し、異なる長さをpaddingで混在させない。

## 取得の契約と実装上の変更

既存8項目の実装は、旧/new adapterのparityを確認するため、過去の88行layoutを
繰り返し実行した。項目の平均総時間は951.81秒で、そのうち771.64秒が旧layoutの
forwardだった。384項目の設計は16行の測定layoutと局所不変条件をすべて保ち、
88行の比較を毎targetでは繰り返さない。これは実測時間に基づく実行上の変更であり、
効果量に基づく変更ではない。この軽量化したrunnerは **まだ実装・計時していない**。

target・carrierごとのforward予定を固定する：

1. Stock glyph、adapter-idle glyph、donor-0 capture、donor-1 capture、
   codepoint reset captureを、それぞれ1 sequenceで実行する。
2. Activeの16行extension batch、その後に同じ16行のneutralを実行する。
3. 介入hookを閉じた後、完全なstock-glyph replayとtarget alias forwardを、
   それぞれ1 sequenceで実行する。alias採用前に完全なstock状態の一致を必須とする。

targetあたり18 call / 78 sequence forwardになる。128 source aliasを両carrierで
再取得すると、256のsingle-sequence callが加わる。
合計予定は **7,168 call / 30,208 sequence forward**。生成、学習、tokenizer呼出し、
codepoint gallery、restoration実験は含めない。
新しい取得結果の代わりに過去のreadoutやaliasを流用しない。

元のcanary schemaにある非legacyの26配列を各項目で保存する。
内訳はstock/codepoint状態、reset capture、donor K/V、active/neutral readout、
実際に使ったattention weightsと局所baseline、位置mask、attention mass。
target/source alias行、すべての検査・回数・時間・content hashも保存する。
このschemaに保存されていない旧完全hidden-state比較は、過去の取得時assertionとして
残り、receiptだけから再構成することはできない。

target 8を処理する前に、新runnerは元のCPU canaryの **index 0–7の全26保存済み非legacy
配列** と8 targetのalias行に、両carrierを含め完全一致しなければならない。
128 sourceの両carrierのalias行も、保存済みCPU取得結果との完全一致を必須とする。
この8 targetは384 runの一部なので、call数は予算に含まれている。
これは算術・実装のgateであり、効果の符号によるgateではない。
不一致なら取得と解釈を止め、有利な効果を理由に免除しない。
過去RTX 5090とのreplayは、別の未実施検査として残る。

モデルは `mlx-community/Llama-3.2-3B-bf16`、revision
`60a99aaf43164077157d64bf909b7b61143c6a6d`、manifest
`dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`
を保つ。取得前後の9-file manifest、Torch 2.13.0+cpu、Transformers 5.15.0、
NumPy 2.5.4、BF16 eager attention、CPU thread 4、interop thread 1、
seed 2026092100を必須とする。cache・量子化・remote codeは使わず、model processは1つ。
実際のPython/platform/attention実装の詳細は、今後の実行manifestに結び付け、
互換性のある完全replayを必須とする。

## 新しいrunより前に固定する測定・集約・報告

final norm後の最後のcarrier tokenを読み出す。自項目aliasを先頭に置き、
変更していない128 source aliasに対するfloat64 L2正規化cosineを使う。
top-1の同点はown-first argmaxで処理し、rankは厳密に大きい競合score数+1とする。
最大競合の同点は元のsource順で最初のものとする。
全scoreを `[384, 2 carrier, 2 active/neutral, 16行, 129]` の形状で保存する：
**24,576行、3,170,304 cosine**。

各scalar metricで `E = active - 同一slotのneutral` を先に計算し、その後平均する。
target・operation Xごとに：

- 位置調整済みdecrement：`Delta_X = mean_carrier,donor(E_suffix,X - E_glyph,X)`。
- 絶対glyph decrement：`-mean_carrier,donor(E_glyph,X)`。
- 非加算性：`Delta_KV - Delta_K - Delta_V`。

位置調整済みmargin decrementが正なら、suffix置換よりglyph置換の方が自項目対最大競合
marginを大きく減らす。reference・K・V・KVをすべて並べる。
**単位はtarget項目でn = 384**。carrier/donorの反復を1,536個の独立項目とは数えない。
それぞれの行を保存し、hidden stateを先に平均してからscoreを計算しない。

own cosine、最大競合cosineとidentity、自項目−競合margin、対応するdonor cosineとmargin、
own rank、own-first top-1を保持する。数値効果の要約には、全項目値、平均、中央値、
標本SD（`ddof=1`）、範囲、正/ゼロ/負の件数、経験的2.5/25/50/75/97.5 percentile
（`numpy.quantile`、`method="linear"`）を使う。Quantileは項目間のばらつきであり、
**信頼区間ではない**。競合IDはcategoryであって数値効果のendpointではなく、
identityと遷移を保存する。Cosine-margin平均の符号からrank/top-1の結果を推定しない。

全384項目の比較を主な記述とする。両carrierを別々に、またglyphの2/3-token群を
診断として示し、すべてのoperationと固定donorを維持する。
これらの層は新しい検定や選別を認めるものではない。
p値、母集団区間、実用効果の閾値、統計的勝者、確認的判定は設けない。
途中の結果によって新しいlayer・donor・metric・除外を選ばない。

marginをown−最大競合に厳密に分解する。block/headごとの実際のattentionと局所baseline、
active対neutralのheadごとのL1距離、glyph/suffix attention massを保存する。
referenceのゼロ効果と局所V attentionの一致は完全一致で検査する。
`1e-12` は独立したfloat64算術再構成の許容差だけに使い、有効性の閾値にはしない。
科学的解釈の前に、独立実装による保存配列とmetricの監査を通す。
384項目のpanelが未完了の間は途中の効果要約を発表しない。
進捗報告には実装検証状態、項目数、時間、メモリ、失敗を記載できる。

## 実行予算・一時停止・回復

alias前の14 callに対応する既存実測stageの合計平均は、canary項目あたり136.53秒だった。
その平均を384項目へ拡大し、alias時間のproxyを加えると **約14.8時間**。
最も遅いcanary項目で拡大すると **約21.7時間**。
旧実装検証layout全体を繰り返す場合は、同じ計算で **約101.7時間**。
これは計画上のscenarioであり、新実装での計時や信頼限界ではない。
alias proxyは、実測288-forwardの経過時間を1,792/288倍し、過去のload/最終manifest検査の
時間も含む。新しい項目形状、資源、model load、filesystem処理、検証でwall timeは変わりうる。

累積稼働時間上限48時間、1 invocationあたり最大8稼働時間、process RSS 20 GiB未満、
開始/再開時の空きdisk 20 GiB以上、run artifact最大10 GiBを固定する。
実行実装はこれらの制限を守り、項目境界でcheckpointし、中断時の稼働時間を実行台帳に
記録しなければならない。不明な中断時間は再開前に解決する。
予算・資源によるpauseは完成chunkを保持するもので、科学的失敗・完了・項目除外の
根拠ではない。予算の改訂は途中の効果を見ることなく、続行前に記録する。

再開できるのは、設計・実行source・runtime・model・入力・batch layoutが同じ未完了作業
だけで、完成chunkをすべて再hashする。runの排他的所有と、項目のatomicな公開を使う。
完了済みの作業は不変とする。Hash/runtimeの不一致、非有限状態、parity/不変条件の失敗では
科学的解釈を停止し、原因を調べる。修正には新versionと証拠互換性の明示が必要で、
古いreceiptや凍結sourceを書き換えない。

## 今回の凍結が認める範囲

[仕様tool](../scripts/t22_kv_exploration_spec_v0.py)は明示的に固定した過去の仕様・receipt・
source file・保存済みreplay配列のcontent hashだけを読む。
語彙scoreの閲覧、再tokenize、新しいpanel選別、model download、model forwardは行わない。
正確なtoken列・donor・行順序・metric・runtime要件・資源方針・実測時間からの見積もりを
凍結する。その監査は設計を決定的に再構成するもので、独立した実験再現ではない。

設計では `execution_admission.admitted=false` とし、新runnerと解析のhashはnullにする。
384-runの取得前に、それらを実装・検証し、この設計と実際のruntimeに正確なhashを
結び付けた実行manifestを公開する必要がある。target 8より前に最初の8項目のreplay gateを
通過しなければならない。設計を凍結しただけで、未検証の軽量化実装を実行可能とは扱わない。
ここでの実行未承認は、ユーザーの追加承認待ちではなく、この技術的検証が未完了という意味。

repo rootで未使用の出力先を使う：

```bash
python3 scripts/t22_kv_exploration_spec_v0.py validate \
  --output validation/t22_kv_exploration_cpu_v0/design_validation.json
python3 scripts/t22_kv_exploration_spec_v0.py freeze \
  --validation validation/t22_kv_exploration_cpu_v0/design_validation.json \
  --output validation/t22_kv_exploration_cpu_v0/specification.json
```

既存の凍結を、外部に記録したSHA-256で監査する：

```bash
python3 scripts/t22_kv_exploration_spec_v0.py audit \
  --specification validation/t22_kv_exploration_cpu_v0/specification.json \
  --expected-sha256 RECORDED_SPECIFICATION_SHA256 \
  --output /tmp/t22-384-design-audit-NEW.json
```

[設計検証](../validation/t22_kv_exploration_cpu_v0/design_validation.json)、
[凍結仕様](../validation/t22_kv_exploration_cpu_v0/specification.json)、
[設計監査](../validation/t22_kv_exploration_cpu_v0/design_audit.json)に今回の段階を記録する。
K/Vの意味的分離、絵文字特異性、intact文脈での必要性・十分性、行動、新たな確認実験は
引き続き未確立。
