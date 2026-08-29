# Emoji Steering Specificity Analysis v0 — T13-EA

[English](EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0.md) · [収集protocol](EMOJI_STEERING_SPECIFICITY_HARVEST_V0.ja.md) · [問いの設計図](EMOJI_STEERING_SPECIFICITY_ATLAS_V0.ja.md)

状態: **outcomeを開く前に固定した、探索的解析の契約**。

T13-EAは、固定済みのT13-EH harvestを解析する。新たなmodel forwardやgeneration、
保護targetの利用、確認的な判定は行わない。Response ledgerのmetric、activation、logit、
科学的な順位を一度も開いていない段階で、この契約を固定した。

## 科学値を開く条件

科学値を開くには、同じprocess内で次の条件をすべて満たす必要がある。

1. 9 roleのdirectory treeが、登録どおりに完走している。
2. 198個のreceiptと、そこに紐づく954個のpayloadが、指定pathに過不足なく存在する。
   余分なfile、symlink、path traversal、未完stageは認めない。
3. Baseline、source、responseの各artifactで、filename、dtype、shape、行数が登録値と
   一致する。
4. 申告済みSHA-256を独立に再計算する。
5. 許可された全fileを束ねるrun-binding rootを、run treeの外側に保存する。
6. 収集processが終了し、writerが残っていない。

外部closeoutには、許可された各relative path、byte数、SHA-256を記録する。Analyzerは
科学値を読む前に、同じprocessでcloseoutを再監査しなければならない。

開封後、最初に行うのは3 pilot roleのzero-hook検証である。非zero介入の行より先に、
KL、JS divergence、total variation、logit-delta RMS、top-tail value、CountSketchがすべて
厳密に0であることを確かめる。Baselineと介入後のentropy、argmaxも一致しなければならない。
一つでも外れれば、全familyの科学解析を中止する。

## 固定した出力family

### F1 — Item単位のsource-form contrast

Item介入は、depth fraction 0.50、magnitude 0.25、正負両符号、公開済み32 target、
3 pilot roleに固定する。比較はmodel、item、target、signの中でpairedに行う。

- Glyph minus Unicode nameは、modelごとに全192 itemを使う。
- Glyph minus decomposed formは、atomic以外の168 itemを使う。
- Unicode name minus decomposed formも、同じ168 itemを使う。
- Atomic anchorにdecomposed formがないのは構造的欠測であり、補完しない。

区間を計算する場合は、事前に固定したitem × targetのpaired cluster bootstrapを使う。
Model roleはpoolせず、roleごとに報告する。

### F2 — Prototypeのdepth / dose surface

登録済みのmodel × glyph system × 利用可能なsource form × target × depth × magnitude × signを、
全cellそのまま残す。Depth surface全体は記述結果であり、都合のよいlayerを選ぶためには
使わない。

非負のscalar endpointでは、dose orderingをraw endpointで測り、正負のpairから効果量の
対称性を調べる。符号を持つentropy changeでは、`sign × entropy_change`でdose orderingを
測り、scalarの反対称性もentropy changeだけで評価する。CountSketchのsign reversalは
F5で扱う。KLやJS、TV、RMSのような非負量から、directionの符号反転は主張できない。

### F3 — 正方向isotropic random calibration

Random armにあるのは、正方向のstandard-normal directionだけである。したがって、登録済みの
random calibrationは、model、target、normalized depth、magnitudeを揃えた正符号prototypeに
限る。負符号のprototypeもsurfaceには残すが、「sign-matched random nullがある」とは扱わない。

このnullは、unit-RMS scaling後のnormを揃えたものにすぎない。Activation covarianceや
activation manifold、負方向にはmatchしていない。

### F4 — Target sensitivity

保存済みbaseline logitから、targetごとのentropyとtop-two logit marginを算出する。
Intervention gridは、まずtargetごとに一つのresponse profileへ畳み込む。行数の異なるgridは
poolしない。Spearman associationとtarget-group heterogeneityはsensitivity診断であり、
source specificityの証拠ではない。

### F5 — Output direction

CountSketch vectorとtop-token IDは、同じmodel内でのみ比較する。Cosineは比較時にだけ正規化し、
zero-norm sketchでは未定義とする。Top-positive / top-negativeは順位上のtailなので、値の符号を
仮定せず、実測したsign purityを併記する。

Sign pairでは`cos(S+, -S-)`と、正負tailを入れ替えたoverlapを報告する。Model横断では、
logical keyを揃えたscalar conditionの順位だけを比較できる。Vocabulary IDやsketch bucketを
直接比べてはならない。Random seedはrole名を含むため、model間でrow単位に対応づけない。

### F6 — Source geometry

9 roleすべてのsource bankから、model内のsource-form cosine、wrapper dispersion、固定8 depthの
trajectory、tokenizerのcount-signature strataを報告する。最初に、保存済みdirectionが4本の
wrapper deltaの平均と一致することを独立に確かめる。

Tokenizer preflightに保存されているのはtoken数とcount signatureであり、正確なtoken IDや
prefix sequenceではない。したがってT13-EAで言えるのは**count-signature matched**までで、
exact-token matchedとは呼ばない。異なるmodelのhidden vectorも直接比較しない。

## 実行stage

解析は、次の二段階に分ける。結果を見て内容を変えることはない。

1. 決定論的なintegrity checkと、全familyのpoint estimate導出。
2. 登録済み20,000 replicateのbootstrap。固定chunkに分け、chunk ID順のSHA-256 manifestで
   決定論的にmergeする。

Bootstrap完了前にpoint estimateを確認してもよいが、後からconfidence intervalが付いたことには
ならない。論文に載せる区間は、登録chunkがすべて揃い、merge検証を通るまで未完扱いとする。
Outcomeを使ってfamily、role、glyph system、target group、depth、magnitude、sign、endpointを
選び直したり、救済したりしない。

## 解釈の境界

T13-EHでは、source directionをunit RMSへ正規化した後、target activationのscaleに合わせている。
測っているのは、この人為的なscaleの下でのorientationであり、自然なencoding strengthや
source efficiencyではない。

今回含まれるcontrolは、Unicode name、利用可能なdecomposed form、正方向isotropic random、
zero directionである。Matched ordinary text、matched non-emoji Unicode、orthogonalized randomは
含まれない。大きく整った結果が出ても、主張できるのは、3 pilot roleにおいて固定済みcontrolと
比べた探索的なintervention-distribution差までである。絵文字の意味理解、絵文字だけに固有の
specificity、自由生成behavior、mechanism、tokenizer非依存性、scale law、model populationへの
一般化、独立確認は確立しない。

Null、heterogeneous、構造的欠測、失敗cellはすべて残す。T13-Cへ進む場合は、新しい未使用target
bankと新たなfreezeが必要になる。T13-EHの観測値をconfirmatory statisticへ混ぜてはならない。
