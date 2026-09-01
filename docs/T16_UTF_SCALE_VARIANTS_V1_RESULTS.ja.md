# T16-UTF-X1 系列長・並び方ストレステストの結果

[English](T16_UTF_SCALE_VARIANTS_V1_RESULTS.md) · [固定済みプロトコル](T16_UTF_SCALE_VARIANTS_V1.ja.md) · [Compact analysis](../validation/t16_utf_scale_variants_v1/results/analysis.json) · [Closeout](../validation/t16_utf_scale_variants_v1/closeout.json)

## 結果の要約

完全同一反復、同一構成内の混合、構成横断の混合を分けるという先行T16-UTFの結果は、
大幅に広げたストレステストでも残った。T16-UTF-X1では、固定した9つのmodel/tokenizer
cell、4深度、`n=500`までの19系列長、6つのUnicode構成system、6種類の並び方、
5種類のseparator、3つの単一anchor位置を組み合わせ、515,808件を完走した。
主要な横断−同一構成の集約は36 / 36 model-depth cellで正となり、system層化bootstrap
区間も全36 cellで0を上回った。0でない18系列長を個別に見ても、`n=500`を含め、
すべての長さで36 / 36 cellの符号が正だった。ただし単調なscale曲線ではない。
全長さを一段ずつ増加し続けたcellは0だった。

さらに、完全に同じmultisetを並べ替えるorder対照から、別の明瞭なパターンが出た。
同じitemを連続した塊にまとめる`blocked`は、72 / 72 model-depth-family cellで
order変位が最大だった。Order pair全体の99.75%はfull-prompt token multisetまで
完全一致している。Anchor位置とseparatorにも差はあったが、系列長との関係や
tokenizer対照の強さはorder laneと異なった。ここで示したのは探索的な隠れ状態幾何で
あり、tokenizer非依存のUnicode構造、絵文字の意味、scale則、因果回路を示す結果ではない。

## 完了した実験面

- Qwen2.5の4サイズ、OLMo 2 1B、SmolLM2 1.7B、Gemma 2 2B IT、
  Llama 3.2 3B、Mistral 7B Instruct v0.3の9 cell。
- 1モデル57,312 record、57,120 unique prompt。全体では515,808 record、
  model×chunk単位で514,080 unique prompt。
- 正規化深度0.25、0.50、0.75、1.00のraw decoder-block outputを、全wrapperで
  共通する最後のtoken位置から取得。
- 生成呼び出し0、介入0。
- 全99 atomic chunkについて、ledger件数、hidden shape、finite値、file hashを確認して
  から統合結果を開封。

9 cellには、学習データやtokenizerの系譜を共有する組み合わせが含まれる。
したがって9つの独立再現とは数えない。また、モデルごとの隠れ状態距離を共通の絶対尺度
として比較しない。

## Scale lane：構成横断の上乗せは長い系列でも残った

表の各値は、system×rotation×wrapperからなる96 principal unitの中央値である。
各unitでは、0でない18系列長を先に平均した。角括弧内は、systemで層化した10,000回
bootstrapによるequal-tailed 95%区間を示す。

| モデル | 0.25 | 0.50 | 0.75 | 1.00 |
|---|---:|---:|---:|---:|
| Gemma 2 2B IT | `0.020312` [0.017202, 0.025056] | `0.058764` [0.050896, 0.069032] | `0.049046` [0.036993, 0.055737] | `0.008846` [0.007089, 0.010369] |
| Llama 3.2 3B base | `0.026651` [0.023856, 0.028785] | `0.039728` [0.030946, 0.044741] | `0.027569` [0.022443, 0.030803] | `0.017638` [0.016450, 0.020952] |
| Mistral 7B Instruct v0.3 | `0.034532` [0.030893, 0.037246] | `0.044824` [0.040131, 0.048745] | `0.050963` [0.044785, 0.057629] | `0.044963` [0.037655, 0.054033] |
| OLMo 2 1B base | `0.020657` [0.019697, 0.022988] | `0.033857` [0.030269, 0.035322] | `0.027274` [0.024622, 0.030640] | `0.016683` [0.014908, 0.019532] |
| Qwen2.5 0.5B base | `0.010588` [0.009715, 0.012951] | `0.013317` [0.010426, 0.015523] | `0.011273` [0.009704, 0.012597] | `0.016596` [0.013864, 0.021645] |
| Qwen2.5 1.5B base | `0.009861` [0.007280, 0.011371] | `0.012645` [0.010250, 0.015391] | `0.015657` [0.012144, 0.019857] | `0.016580` [0.014121, 0.019964] |
| Qwen2.5 3B base | `0.017373` [0.014882, 0.018959] | `0.014943` [0.013301, 0.016897] | `0.016141` [0.013709, 0.017549] | `0.011379` [0.009923, 0.013163] |
| Qwen2.5 7B base | `0.023156` [0.020300, 0.027325] | `0.025414` [0.021644, 0.029092] | `0.031505` [0.022767, 0.033990] | `0.025975` [0.025356, 0.033461] |
| SmolLM2 1.7B base | `0.006857` [0.006257, 0.007531] | `0.012381` [0.011084, 0.014369] | `0.010516` [0.009138, 0.011179] | `0.011871` [0.008253, 0.013221] |

`n=500`でも、横断−同一構成は36 / 36 cellで正だった。値の範囲は`0.010529`から
`0.069266`。正のprincipal unit数は78 / 96から96 / 96で、中央値は92 / 96だった。
集約した符号は安定しているが、unit間のばらつきまで消えたわけではない。

系列長との関係は単純なscale則ではなかった。`n=256`が`n=16`を上回ったのは30 / 36、
`n=500`が`n=16`を上回ったのは27 / 36 cellだった。一方、`n=384`から`n=500`へ
さらに増えたのは17 / 36にとどまり、0でない18長さを通して単調非減少だったcellは0。
最大値の位置は`n=384`が13 cell、`n=500`が9、`n=256`が6で、残り8 cellは
さらに短い位置だった。Qwen2.5の4サイズも、parameter数順に厳密に並んだのは
0.75深度だけである。長系列でもパターンが残ったとは言えるが、系列長やparameter数の
scale則とは言えない。

親実験T16-UTFで使ったGemmaとMistralについては、`n=2,4,8,16`を再取得した
32 model-depth-length cellすべてで符号が一致した。各`n`中央値の最大絶対差はGemmaで
`0.002347`、Mistralで`0.001339`。Batch構成の異なる再取得における記述的な一致であり、
事前に閾値を決めた数値parity testでも、独立再現でもない。

## 完全同一multisetのorder対照：連続blockが最大だった

Order pairではanchorを必ず先頭に残し、UTF item multisetを完全に揃えた。同じfamily、
長さ、separator、wrapper、anchorのまま、forward cycleに対してreverse、連続block、
両端interleave、固定seedによる2種類のshuffleを比較している。

9モデルを合わせた259,200 pairのうち258,544件、99.7469%はfull-prompt token
multisetまで完全一致した。8モデルでは28,800 / 28,800 pairがすべて一致した。
Gemmaは28,144 / 28,800で、contrast別一致率は95.56%から100%だった。

特に揃っていたのは次の3点である。

- 同じglyphを連続した塊にする`blocked_tail`が、72 / 72
  model-depth-within/cross cellで最大変位になった。次に大きいorder variantとの比は
  中央値1.88倍、範囲1.07〜4.81倍。
- 構成横断orderの変位が、180 / 180 model-depth-order-variant比較で同一構成内を
  上回った。
- Blocked変位は、72 / 72 model-depth-family cellで`n=256`が`n=8`を上回った。
  Reverseやinterleaveには、この一様な蓄積はなかった。

このlaneは、token inventoryを固定しても、tokenの順序と局所的なまとまり方によって
取得状態が変わることを強く示す。ただしscale laneのtokenizer境界を解消する結果ではなく、
Unicode familyの意味を同定した結果でもない。

## 単一anchorの位置：末尾ほど大きいが、長さとともには増えにくい

Position laneでは、同一構成内または構成横断の固定backgroundに、完全一致するanchorを
1件だけ置き、先頭・中央・末尾を比較した。Pair間のUTF item multisetは同一である。

- Cross backgroundの変位は、72 / 72 model-depth-position比較でwithin backgroundを
  上回った。
- Anchorを末尾へ動かした変位は、71 / 72 model-depth-family cellで中央より大きかった。
  唯一の逆転はQwen2.5 0.5Bの最終block、cross backgroundで、middle `0.016530`、
  last `0.016377`だった。
- Blocked orderとは違い、位置効果は長さとともに増えることが少なかった。`n=256`が
  `n=8`を上回ったのは、within-middle 0 / 36、within-last 6 / 36、
  cross-middle 2 / 36、cross-last 8 / 36だった。

Full-prompt token multisetが一致したのは77,952 / 103,680 pair、75.19%。Mistralは
11,520 / 11,520 pairがすべて一致した。他モデルの集約一致率は63.33%から88.33%だった。
したがって、同じtoken inventoryの置き場所だけで取得状態が変わることを最もきれいに
示すのはMistral cellである。モデル横断の集約は引き続きtokenizer条件付きとする。

## Separator：効果は大きいが、tokenizerからは分離できない

Separatorなしとの比較では、newlineが36 model-depth cell中26で最大、comma-spaceが6、
ASCII pipeが4だった。ASCII spaceが最大のcellは0。0.25深度では9 / 9、0.50深度では
8 / 9モデルでnewlineが最大だった。Separator変位は系列長とともに増える傾向があり、
`n=256`が`n=8`を上回ったのはASCII space 36 / 36、comma-space 32 / 36、
newline 32 / 36、pipe 29 / 36 cellだった。

一方、full-prompt token multisetが一致したseparator pairは0件だった。見えるdelimiterを
加えた効果とtokenizer経路の変化が混ざっているため、tokenizer非依存の句読法幾何とは
解釈しない。

## Tokenization境界と構成system間のばらつき

Scale pairでは、full-prompt token multisetが一致した例はない。Within-familyの
Qwen pairではtoken数一致が多かったが、cross-familyの一致は疎で、Gemmaの28.24%から
Qwenの0.93%までだった。したがって36 / 36というscaleの符号だけから、Unicode構成family
の差がtoken identityを揃えても残るとは言えない。

構成system間にも差がある。横断−同一構成のsystem中央値が最大だったのは、keycapが
25 / 36 cell、regional-indicator flagが8、presentation sequenceが3。Qwen2.5 0.5Bの
後期2 cellではatomic scalarのsystem中央値がわずかに負だった。96 unit全体のcell中央値は
どちらも正だが、すべての構成systemが全深度で一様に正だったわけではない。

## 実行上の但し書き

科学runはpush済みのfreeze commit `fcf73bd`から実行し、8,039秒で完了した。
CUDA allocatorのretry警告は6件あり、Gemmaで3件、Qwen2.5 3Bで1件、Qwen2.5 7Bで2件。
Python例外や未完chunkにはならず、採用した全arrayはその後のfinite値、shape、row count、
SHA-256検証を通過した。警告は実行logとcloseoutに残しており、無警告runとは記述しない。

Commit `7a99494`から走らせた先行engineering canaryは、より大きなpadded-token budgetを
使っていた。これはengineering-invalid evidenceとして保存し、科学結果から完全に除外した。

## 主張境界とエビデンス

T16-UTF-X1にはbinaryな科学gateを置いていない。最も強い結果は、tokenizer条件付きの
分離が長系列でも安定していたことと、ほぼ完全なtoken-multiset対照のもとでorder効果が
見えたことである。絵文字の意味、因果実装、tokenizer非依存のUnicode構成、
instruction tuning効果、parameter scale則、モデル母集団への一般化は主張しない。

- [Compact analysis](../validation/t16_utf_scale_variants_v1/results/analysis.json)、SHA-256 `988f2689565b9d45741f8f342cf49a3b54bd3d8d88f570f1693f21756f6d3e12`
- [Closeout](../validation/t16_utf_scale_variants_v1/closeout.json)
- [Execution log](../validation/t16_utf_scale_variants_v1/run.log)、SHA-256 `9e09603ea4771c5552b9e27c66e33438858120617dc3c053a4b4e0643cb55b0d`
- [Tokenizer preflight](../validation/t16_utf_scale_variants_v1/tokenizer_preflight.json)

20.31 GBのraw runは記録済みの炉上scratch rootに残し、生のhidden arrayはGitへコピーして
いない。
