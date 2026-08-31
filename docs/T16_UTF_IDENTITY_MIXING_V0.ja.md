# T16 完全UTF同一性・混合・sequence長

T16-UTFは単純な番外問いを分離する。Sequenceが同じ完全emoji文字列の反復、同じUnicode
construction family内の異なるemoji文字列、construction familyを跨ぐemoji文字列から成るとき、
何が変わるか。

## 正確なsequence構成

Panelは6 construction familyごとに完全な4文字列を固定する。単一scalarのatomic glyph、
base-plus-VS16 presentation sequence、skin-tone modifier sequence、3 scalar ZWJ sequence、
regional-indicator flag、digit keycapである。Code pointを明示保存し、各UTF-8文字列と照合する。

各familyと4 rotationについて、`clone_exact_utf`は一つのanchor文字列をbyte-for-byteで反復する。
`within_system_mix`は同familyの4文字列をcycleする。`cross_system_mix`は同じitem rotationを使い、
6 familyをcycleする。Separatorは空文字列で、全条件の先頭は完全に同じanchorである。n=1では
3条件が同じunique promptへcollapseする。Sequence長は1、2、4、8、16、wrapperは固定4種である。

## Captureと解析

Gemma 2 2B ITとMistral 7B Instruct v0.3を固定causal-language model artifactとして使うが、
promptはchat instructionではなくraw wrapper文字列である。最後の共通wrapper tokenにおける
raw decoder-block outputを、正規化depth 0.25、0.5、0.75、1.0でcaptureする。

完全factorialはmodelごとに1,440 recordだが、n=1の3条件が同じpromptを共有するためunique prompt
は1,248件である。Runnerはunique promptを一度だけcaptureし、3 recordを同じarray rowへmapping
する。これによりn=1 equalityは正確な構成invariantになる。

Model、depth、family、rotation、wrapperごとに次を報告する。

- clone growth: n=1 cloneからnのcloneへのcosine distance。
- within-family extra displacement: family内mixと同じnのcloneの距離。
- cross-family extra displacement: family間mixと同じnのcloneの距離。
- cross-minus-within displacement。

Primary descriptive summaryは各endpointをn=2、4、8、16で平均し、6 construction familyで
stratifyした20,000 replicate bootstrapを付ける。全n別値と、完全token-count matched pairを
全て保持する。

## Claim境界

完全UTF同一性は、混合後のtokenization一致を意味しない。Preflightは全recordについてtoken数、
UTF-8 byte数、scalar数、sequence hashを記録する。Token-count matched subsetは記述的であり、
不利な結果の救済には使えない。本研究は観測tokenizer pathのもとでのhidden-state geometryを
記述し、tokenizer-independentなUnicode composition、emoji意味、因果回路を証明しない。

