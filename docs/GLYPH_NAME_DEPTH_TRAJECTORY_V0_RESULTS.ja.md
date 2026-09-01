# T17-GN glyph–name 深度軌跡の結果

[English](GLYPH_NAME_DEPTH_TRAJECTORY_V0_RESULTS.md) · [固定protocol](GLYPH_NAME_DEPTH_TRAJECTORY_V0.ja.md) · [Compact analysis](../validation/glyph_name_depth_trajectory_v0/results/analysis.json) · [独立検収](../validation/glyph_name_depth_trajectory_v0/independent_validation.json) · [Closeout](../validation/glyph_name_depth_trajectory_v0/closeout.json)

状態：**T9/T10ですでに開いた項目を使う探索atlasとして完了**。

## 一段落でいうと

Raw emoji surfaceは、固定した9モデルすべてで、literalな`U+...` codepoint列よりも
Unicode正式名をitem単位で引き当てやすい状態へ進んだ。ただし、全モデルに共通する
「後期層での一斉転換」は見つからなかった。2 carrier × 4 distanceを等しくまとめた
forward top-1差は、正規化深度`0.375`以降、9 / 9モデルで正だった。Item単位の
20,000回bootstrap区間は、深度`0.50`、`0.75`、`0.875`、`1.0`で9 / 9モデルとも
下限が0を上回り、token数を完全一致させた点推定も`0.25`以降は9 / 9で正だった。
一方、peakは最初のblockが2モデル、`0.125`が1、`0.75`が1、`0.875`が5と分かれた。
最終状態では、対応itemと非対応itemを分けるcosine marginは9 / 9でnameを支持したが、
空間全体を見るcentered linear CKAは4 / 9にとどまった。したがって守れる結論は、
**item固有の語彙ラベル検索は広く収束するが、立ち上がり方はmodel固有で、表現空間全体が
同じ形へ揃うわけではない**、までである。

![9モデルのglyph-to-name深度軌跡](../validation/glyph_name_depth_trajectory_v0/results/depth_curves.svg)

## 何を比べたか

292項目には、次の3つのtext viewを固定した。

1. raw Unicode emoji surface
2. Unicode正式名
3. literalな`U+...` codepoint列

ここでいう「glyph」は、各modelのtext tokenizerへ渡したraw Unicode文字列である。
Font画像をrasterizeしてvision modelへ見せた実験ではない。Headlineは、modelとdepthごとに、
emojiから正しい正式名をforward top-1で検索できた割合から、正しいcodepoint literalを
検索できた割合を引き、2 carrier × 4 distanceを等weightで平均した値である。正の値は、
この固定hidden-state幾何のもとで、正式名の方がcodepoint列より正しいitemを引き当てやすい、
ということだけを表す。

項目集合はT9/T10ですでに開いている。T17-GNの深度設計はoutcome取得前に固定したが、
独立確認ではない。

## 完了した取得

| 監査項目 | 結果 |
|---|---:|
| Exact model/tokenizer role | 9 / 9 |
| 各roleの項目数 | 292 |
| View | 3 |
| Context | 2 carrier × 4 distance |
| 正規化深度 | 9（`0.0`〜`1.0`） |
| 完了shard | 90 |
| Model forward | 15,768 |
| FP32 readout vector | 567,648 |
| Generation / intervention | 0 / 0 |
| 取得時間 | 136.388秒 |
| 記録上の最大peak CUDA割当 | 15,319,300,608 byte |

最終fractionはAPIが返すfinal hidden stateで、model-final normalizationを含み得る。
中間fractionは、各architectureで解決したdecoder block後のhidden stateである。
この二つを同じendpointとして曖昧に扱っていない。

## Modelを横断した軌跡

Modelごとの区間は、8 contextをitem内でまとめたまま、itemを20,000回resampleしている。
下表はmodel横断の記述的な断面であり、別の推論familyではない。

| 正規化深度 | 中央値 | Model間range | 正の点推定 | Bootstrap下限が正 | Token数一致で正 |
|---:|---:|---:|---:|---:|---:|
| 0.000 | 0.007277 | -0.001712〜0.178938 | 5 / 9 | 5 / 9 | 6 / 9 |
| 0.125 | 0.025257 | -0.002140〜0.139127 | 8 / 9 | 6 / 9 | 8 / 9 |
| 0.250 | 0.031678 | -0.000856〜0.115582 | 8 / 9 | 8 / 9 | 9 / 9 |
| 0.375 | 0.032106 | 0.003425〜0.091610 | 9 / 9 | 8 / 9 | 9 / 9 |
| 0.500 | 0.028253 | 0.010274〜0.105736 | 9 / 9 | 9 / 9 | 9 / 9 |
| 0.625 | 0.029110 | 0.006849〜0.183219 | 9 / 9 | 8 / 9 | 9 / 9 |
| 0.750 | 0.052654 | 0.014127〜0.237158 | 9 / 9 | 9 / 9 | 9 / 9 |
| 0.875 | 0.064640 | 0.019264〜0.235445 | 9 / 9 | 9 / 9 | 9 / 9 |
| 1.000 | 0.054366 | 0.012842〜0.233305 | 9 / 9 | 9 / 9 | 9 / 9 |

共通しているのは、深さとともに単調増加することではない。Modelごとに違う経路を通りながら、
中盤から後半にかけて正の断面へ集まることである。`0.625`では9本中1本の区間下限が再び0を
またぐため、きれいで不可逆な閾値とも呼べない。

## Modelごとの立ち上がりとpeak

「持続CI深度」は、その点から先の全sampled depthでbootstrap区間が0を上回り続ける最初の
深度を指す。「最終minimum」は、最終状態における8 contextのheadline差の最小値である。

| Model | 一致n | 初期値 | 持続CI深度 | Peak深度 / 値 | 最終値 [95%区間] | 最終minimum | 一致層の最終値 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen2.5 0.5B base | 284 | 0.007277 | 0.000 | 0.875 / 0.031250 | 0.017551 [0.008134, 0.027825] | 0.006849 | 0.017606 |
| OLMo 2 1B base | 281 | -0.001712 | 0.250 | 0.875 / 0.036387 | 0.027825 [0.015839, 0.041524] | 0.013699 | 0.030249 |
| Qwen2.5 1.5B base | 284 | 0.126712 | 0.000 | 0.000 / 0.126712 | 0.026969 [0.017123, 0.037671] | 0.013699 | 0.024648 |
| SmolLM2 1.7B base | 287 | 0.000000 | 0.750 | 0.875 / 0.019264 | 0.012842 [0.003853, 0.022688] | 0.006849 | 0.013066 |
| Gemma 2 2B IT | 284 | 0.072346 | 0.000 | 0.125 / 0.139127 | 0.069777 [0.055223, 0.085188] | 0.017123 | 0.073504 |
| Llama 3.2 3B base | 281 | -0.000856 | 0.250 | 0.875 / 0.062928 | 0.054366 [0.034675, 0.075342] | 0.027397 | 0.057829 |
| Qwen2.5 3B base | 284 | 0.178938 | 0.000 | 0.000 / 0.178938 | 0.067637 [0.053082, 0.083476] | 0.017123 | 0.070423 |
| Qwen2.5 7B base | 284 | 0.068065 | 0.000 | 0.875 / 0.229880 | 0.102740 [0.080908, 0.125428] | 0.023973 | 0.106514 |
| Mistral 7B Instruct v0.3 | 285 | -0.000856 | 0.125 | 0.750 / 0.237158 | 0.233305 [0.200332, 0.267551] | 0.202055 | 0.237719 |

4つのQwen checkpointだけを見ると、最終値はparameter数の順に大きい。しかし軌跡は揃わない。
1.5Bと3Bは最初のsampled blockがpeakで、0.5Bと7Bは`0.875`がpeakだった。Size、architecture、
training data、checkpoint identityが交絡しているため、scale lawとは呼ばない。

## Item検索と空間全体の整列は別だった

返却された最終状態で、対応itemと非対応itemを分ける
paired-minus-off-diagonal cosine marginは9 / 9モデルでnameを支持した。ところが、同じ
name-minus-codepoint差をcentered linear CKAで測ると、正だったのはOLMo、Gemma、Llama、
Mistralの4モデルだけだった。残る5モデルでは、item検索とpaired marginがnameを支持しても、
CKA差は負だった。

これは重要な分離である。Raw emojiは自分自身の語彙ラベルを引くkeyとして改善できるが、
emoji行列全体がcodepoint行列よりname行列に似た形へ作り替わる必要はない。T17-GNが強く
支持するのは、空間全体の意味manifold収束ではなく、item固有の対応関係である。

## T10最終境界の完全再現

独立compact validatorは、T17 analysis、CSV、SVGを別に検査した。さらに、返却された最終状態の
unrestrictedおよびtoken数一致のcarrier × distance差を、T10で公開したmodel-cell resultと
照合した。`9 × 8`のunrestricted cellと`9 × 8`のmatched cellは、すべてexact replayだった。
これによりT17の深度軌跡は以前の最終状態へ切れ目なく接続する。ただし、T10の登録済み実用条件が
不通過だった判定は変えない。

独立検収では、次も合格した。

- CSV 81行、9本のcurveと81 plot point
- 15,768 forward、567,648 readout
- 6つのclaim authorization flagがすべてfalse
- T10 source result SHA-256
  `aed7c4abf53b349afe762e359e75193e7b129e9f90ff84c813a5e76ca47fbcfb`

## 消さずに残したruntime failure

候補modelのforwardやweight loadより前に、runtime probeが2回停止した。Furnaceのsystem Pythonには
`glyphprobe`がなく、同じinterpreterへ`PYTHONPATH=src`を与えた次のprobeでは`pydantic`が
なかった。科学設計は変更していない。最初の候補forwardには、既存project runtimeのTorch
`2.13.0+cu132`、Transformers `5.15.0`、NumPy `2.5.2`、PyYAML `6.0.3`、GlyphProbe
`0.1.0`を使った。二つの停止は、成功後に消さずvalidation receiptへ残した。

## 主張境界と次のgate

T17-GNが支えるのは、9つのexact model/tokenizer cellにおけるraw emoji surface、Unicode正式名、
codepoint literalの探索的な深度atlasである。視覚的glyph知覚、人間のような絵文字意味理解、
tokenizer非依存性、因果、circuit、instruction tuning効果、parameter scaling、独立再現、
model母集団やemoji母集団への一般化は示さない。

次は、outcomeを見る前に固定した新しい未使用項目集合で確認する。Unicode正式名だけでなく、alias、
paraphrase、多言語名、codepoint literalを分け、tokenization-matched層も保つ。そのgateを通った場合に
限り、model間で共有できる後期windowを選び、name情報の除去・追加・復元を因果的に検定する。

## Evidence

- [Compact analysis](../validation/glyph_name_depth_trajectory_v0/results/analysis.json)、SHA-256 `ed615103d85608893caf207c856a01922a4e744c6f9713f0293aa223bf8139e4`
- [Depth-curve CSV](../validation/glyph_name_depth_trajectory_v0/results/depth_curves.csv)、SHA-256 `806780db8d74e06f038e32820c355d8ef54733530aab59ed2777137dabcd2098`
- [Depth-curve figure](../validation/glyph_name_depth_trajectory_v0/results/depth_curves.svg)、SHA-256 `0733cd392fd856f2874629403b500bb813fc6105be9ee8365ac88c10c3f43428`
- [独立検収](../validation/glyph_name_depth_trajectory_v0/independent_validation.json)
- [Runtime failure receipt](../validation/glyph_name_depth_trajectory_v0/runtime_preflight_failures.json)
- [Closeout](../validation/glyph_name_depth_trajectory_v0/closeout.json)

5.1 GiBのraw hidden-state runは、記録したfurnace scratch pathに残しており、Gitへはコピーしていない。
