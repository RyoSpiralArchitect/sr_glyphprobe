# Emoji Steering Specificity Expansion Analysis v0

[English](EMOJI_STEERING_SPECIFICITY_EXPANSION_ANALYSIS_V0.md) ·
[T14-X取得](EMOJI_STEERING_SPECIFICITY_EXPANSION_V0.ja.md) ·
[T14-C因果path](EMOJI_STEERING_CAUSAL_PATH_V0.ja.md)

Protocol ID: `glyphprobe-emoji-steering-specificity-expansion-analysis-v0`  
実験label: **T14-XA**

T14-XAはT14-Xの科学値を1件も開く前にcomplete-family解析を固定する。6 model・
559,488 response recordがすべてvalidateされるまでは、partial modelのinspectionを
禁止する。

## Headline estimand

各model・depth・target・endpointで、48本のsigned glyph-view wrapper-holdout
system prototypeのmedianから、128本のsigned source-covariance nullのmedianを引く。
主な単位はtarget promptであり、報告するpopulation statisticはrow-levelの擬似反復
meanではなく、32個のtarget-level differenceのmedianである。
Primitiveなargmax-flip rowはbinaryなので、このendpointだけはtarget内でmeanを取り、
その後は同じtarget-level medianを使う。他endpointのtarget内縮約はmedianである。

## Complete family

同じ固定executableが次の7 familyをすべて報告する。

1. structured glyph prototype全体とcovariance nullの比較
2. 6 glyph system別の同じ比較
3. glyph prototypeと利用可能な全non-glyph prototype source formの比較
4. itemを揃えたglyphとUnicode-name / decomposed-form directionの比較
5. headline target estimandのdepth 0.875対1.0
6. Gaussian対Rademacher covariance-null感度
7. structured directionのpositive対negative orientation

すべてのtableに6 model、2 depth、全endpoint、negative/mixed cellを残し、targetを
clusterとする20,000回percentile intervalを付ける。このintervalは記述的な安定性
summaryであり、有意差検定もconfirmatory decisionも行わない。

## Scientific-open境界

Analyzerは自身のfreezeをauditし、その後T14-Xのsix-role run auditorを呼ぶ。両方が
passして初めてscalar response ledgerを読む。Prompt、activation bank、tokenizer、
model、top-k logit array、CountSketch valueは読まない。不完全runはclosedのまま残す。

## Claim境界

T14-XAは、凍結target set上でstructured-versus-null response patternが安定し、
modelを跨いで観察されるかを記述できる。それだけでemoji meaning、understanding、
unique circuit、causality、tokenizer independence、architecture/model populationへの
一般化、scale lawは確立しない。因果gateは別のT14-Cである。
