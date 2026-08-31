# Emoji Steering Causal Path v0

[English](EMOJI_STEERING_CAUSAL_PATH_V0.md) ·
[T14-X拡張](EMOJI_STEERING_SPECIFICITY_EXPANSION_V0.ja.md) ·
[科学的契約](SCIENTIFIC_CONTRACT.ja.md)

Protocol ID: `glyphprobe-emoji-steering-causal-path-v0`  
実験label: **T14-C**

## 因果の問い

T14-Cは「modelがemojiを理解しているか」より狭い問いを立てる。同じsource
residual covarianceから作ったsigned directionと比較して、1つの固定した下流
Transformer componentがlate structured-source output-distribution effectを
選択的に媒介するかを調べる。

CellはT14-X outcomeより前に固定する。Llama 3.2 3B base、BF16、
Transformers/CUDA、`resid_post` block 23（normalized depth 0.875）への
unit-RMS magnitude 0.25介入、sole primary endpointはnext-token
Jensen–Shannon divergenceである。

## 二段階の分離

Component選択と因果確認を分ける。

1. **Localization:** 既に公開済みの32 targetで、block 24〜27の`attn_out`と
   `mlp_out`、合計8候補を比較する。Block 24 `resid_pre` patchをpositive
   erasure control、block 22 `mlp_out`をupstream temporal shamとする。
2. **C1 v2 confirmation:** 凍結済みselectorでeligibleな候補を1つだけbindし、
   そのbindingをcommit/pushした後で初めて新しい192-target bankをmaterialize
   する。Localization中にはbankを生成しない。

Selectorは、target-level structured-minus-null necessity excessの中央値が最大の
eligible候補を選び、同値なら固定したsite順で決める。Scoreが負でも探索をやり直さず、
最上位のeligible siteをC1 v2へ持ち込む。Engineering fidelityを通るsiteが1つも
なければ、bankを生成する前にfail closedする。

## 介入とcontrol

各targetには80個のsigned treatment conditionを与える。

- 24 leave-one-wrapper-out glyph-system prototype × 2 sign
- 16 source-covariance null × 2 sign

各treatmentとcandidate componentについて4 passを残す。

- 通常のtreatment
- **necessity:** treatment componentをpaired baseline値へ置換する
- **sufficiency:** treatment component値をbaseline pathへpatchする
- **restoration:** treatment componentをcaptured treatment値へ戻し、patchの
  round tripを検証する

各condition batchには同一のzero-vector rowを2本入れ、同じbatch内でlogitを比較して
explicit-zero hook gateとする。この2本は80-conditionの科学estimandには入れない。

Localizationは25,600 response record、1-site C1 v2は新規192 target上で
15,360 recordとなる。

## Primary C1 v2 decision

主なsampling unitは192 targetで、12 group ×16件に層化する。Glyph system、
wrapper fold、sign、null seedはtarget内の反復測定である。

各condition familyをまずtarget内で縮約し、192 target全体の固定aggregateとして
medianを使う。Primaryは、次の3つをすべて要求する1つのintersection–union testである。

1. structured treatment minus signed-null treatment: JS lower bound > 0.002
2. structured necessity drop minus signed-null necessity drop: lower bound > 0.0005
3. structured sufficiency minus signed-null sufficiency: lower bound > 0.0005

不確実性は20,000回のstratified target-cluster bootstrapによるtwo-sided
equal-tailed 95% intervalで求める。各componentは、zeroをnullとする99,999回の
paired target sign-flipによるone-sided p値も0.05未満でなければならない。
1 model・1 site・1つの三要素IUTなので追加の多重性補正は行わない。Restoration、
explicit zero、upstream sham gateも必須である。

1要素でも失敗すればT14-Cはnegativeである。別site、endpoint、subset、sign、
source form、depth、modelによる救済は行わない。

## Holdout境界

Retired C1 v1、P2、公開prestage targetはC1 v2に使わない。Deterministicな
C1 v2 generator自体はlocalization前に凍結するが、selected-site manifestと
causal executableのhashがcommit/pushされるまではprompt rowを1件も出力しては
ならない。Materialization時にresearch transcriptへ出すのはrow count、stratum
count、SHA-256、receiptだけとし、prompt本文はone-shot C1 v2が終わるまで表示しない。

## 凍結した実行順

Executableのgateは次の順にしか進まない。

1. `audit-design`、`write-design-preflight`、`freeze`、`audit-freeze`
2. 公開target上の`run-localization`と`validate-localization`
3. `select-site`後、生成されたmanifestをcommit/push
4. protected causal fileについて`HEAD == origin/main`でなければfailする
   `materialize-bank`
5. `run-confirmation`、`validate-confirmation`、最後に`analyze-confirmation`

Localization/confirmation outputはrepo外のatomicかつhash-boundなsite directoryとする。
Model load前、site前、各target前に炉のcontentionを確認し、exit code 75は再開可能な
yieldであって科学的evidenceではない。

## 許される結論

IUTが通れば、selected componentが、この固定cellにおけるoperationalな
structured-versus-null next-token JS effectを因果的に媒介する、と限定して言える。
Emoji meaning、understanding、complete circuit、natural encoding strength、
generated behavior、tokenizer independence、scale、architecture/model populationへの
一般化、independent replicationは確立しない。
