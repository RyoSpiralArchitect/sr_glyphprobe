# Multifamily tokenizer census v0 結果

[English](MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.md) · [固定プロトコル](MULTIFAMILY_TOKENIZER_CENSUS_V0.ja.md) · [研究ロードマップ](ROADMAP.ja.md)

Analysis ID: `glyphprobe-multifamily-tokenizer-census-v0-posthoc-aggregate-v1`

## 結果の位置づけ

3 nodeで行ったtokenizer-only censusは、固定roster 14 entryすべてで完了した。
決定論的な事後collectorが各nodeの台帳を再検証し、`status: pass`のcompactな
集計artifactを公開した。

これはcontrol設計のための記述的な証拠である。Activation、behavior、確認、意味、
因果の結果ではなく、これだけでPhase I論文gateを閉じるものでもない。

## 固定scopeとintegrity

Censusは公開v0 freeze commit
`e3bea44a145d3c87f41fc5c60f90201b8cea2bdc`を用いた。

| Check | 結果 |
|---|---:|
| Node | `mac1`, `mac2`, `furnace` |
| 完了した固定roster entry | 14 / 14 |
| 固定文字列 | 115 |
| 固定tokenization context | 4 |
| Tokenization row | 6,440 |
| Pairwise-control row | 19,665 |
| Model-forward call | 0 |
| Openしたprotected target file | 0 |

Collectorは、集計前に各nodeの`SHA256SUMS`、receipt、summary、row数と、共有する
config、manifest、audit scriptのhashを再検証した。Git artifactには3 nodeのreceiptと
summaryをpath-scrubした複製、公開node bundle用のchecksum台帳、
`SOURCE_SHA256SUMS`という別名で元source checksum台帳、raw tableの正確なhashとrow数を
残した。Collection receiptはscrub前のsource receipt hashを結び付け、公開用複製では
machine-localな絶対pathを固定markerへ置換する。約38 MiBのraw JSONL tableは意図的に
含めていない。Hashだけでは省略dataを復元できない。

Compact bundleは
[`collection_receipt.json`](../artifacts/multifamily_tokenizer_census_v0/collection_receipt.json)
とtop-level
[`SHA256SUMS`](../artifacts/multifamily_tokenizer_census_v0/SHA256SUMS)で結び付けている。
完全な派生tableは
[`aggregate.json`](../artifacts/multifamily_tokenizer_census_v0/aggregate.json)にある。

## 7つの完全一致output class

14 roster entryは、115 itemと4 contextの全記録について、7つの完全一致する
tokenization output classへまとまった。このうち5 classは、2 node以上で完全に再現した。

| Output class | この固定censusで完全一致したmember | Raw平均 | Raw中央値 | Raw最大値 |
|---|---|---:|---:|---:|
| 01 | Furnaceとmac2のGemma 2 | 1.296 | 1 | 7 |
| 02 | Gemma 3 4B/12BとGemma 4 E4B | 1.435 | 1 | 7 |
| 03 | 3 nodeのMistral 7B Instruct v0.3 | 4.791 | 5 | 20 |
| 04 | mac1とmac2のGPT-2 | 3.374 | 3 | 14 |
| 05 | mac1とmac2のLlama 3.2 3B | 3.365 | 3 | 15 |
| 06 | OLMo 3 7B | 3.504 | 3 | 18 |
| 07 | Qwen 2.5 3B | 1.600 | 1 | 10 |

ここでの「完全一致」は、固定した115 item・4 contextのsurfaceで、記録した
tokenization outputが同一だったという意味に限る。一般的なtokenizer同一性、modelの
同等性、このcensus外での一致は確立しない。

## Tokenizer間fragmentation

7 output classすべてでraw token数が同じだったのは、115文字列中6件だけだった。
`control_brackets`、`control_colons`、`control_hashes`、`control_lower_alpha`、
`control_periods`、`keycap_hash_base`である。

Raw token数のclass間rangeは次の分布だった。

| Range | Item数 |
|---:|---:|
| 0 | 6 |
| 1 | 6 |
| 2 | 10 |
| 3 | 3 |
| 4 | 78 |
| 5 | 6 |
| 7 | 5 |
| 13 | 1 |

最大のfragmentationは`zwj_family`で、raw spanは7〜20 tokenだった。これは
tokenizer構造の観測であり、modelがfamily絵文字をより合成的、または非合成的に
表現する証拠ではない。

## Unicode合成

同じtokenizer artifactを独立な証拠として重複計上しないため、合成summaryでは
7つの完全一致output classを1回ずつ重み付けした。

| Construction | 関係 | 観測数 | Histogram |
|---|---|---:|---|
| Keycap sequence | sequence minus base | 14 | `+1`: 4, `+4`: 10 |
| Skin-tone sequence | sequence minus base | 42 | `0`: 1, `+1`: 21, `+3`: 18, `+4`: 2 |
| Variation-selector sequence | sequence minus base | 35 | `0`: 7, `+1`: 28 |
| ZWJ sequence | sequence minus 固定component合計 | 56 | `0`: 8, `+1`: 21, `+2`: 21, `+3`: 3, `+6`: 3 |

これらのdeltaはtoken数だけを記述する。意味の合成や内部featureの合成を測っていない。

## Context感度とround trip

固定glyph-plus-prompt suffixでspan token数が変わったitemはなかった。Llama、OLMo、
Qwen classでは6 itemのspan token IDが変わり、他の4 classでは変化しなかった。
先頭spaceへの感度ははるかに大きく、tokenizer classごとに大きく異なった。

| Output class | 先頭spaceでのID変化 | 先頭spaceでの数変化 | Glyph-promptでのID変化 |
|---|---:|---:|---:|
| 01 Gemma 2 | 26 / 115 | 0 / 115 | 0 / 115 |
| 02 Gemma 3/4 | 25 / 115 | 1 / 115 | 0 / 115 |
| 03 Mistral v0.3 | 106 / 115 | 106 / 115 | 0 / 115 |
| 04 GPT-2 | 115 / 115 | 3 / 115 | 0 / 115 |
| 05 Llama 3.2 | 112 / 115 | 18 / 115 | 6 / 115 |
| 06 OLMo 3 | 112 / 115 | 21 / 115 | 6 / 115 |
| 07 Qwen 2.5 | 112 / 115 | 98 / 115 | 6 / 115 |

このcensusでは、marker wrapperで記録した数変化は全classで先頭space条件と一致した。
これは固定template上の観測であり、wrapper一般に対する不変性の主張ではない。

6,440 rowのうち6,095 rowはencodeしたtextへ完全にdecodeした。非完全一致345件はすべて、
Mistral v0.3の3 labelそれぞれにおける115件の`leading_space` rowだった。Collectorはrowを
削除もtokenizerの差し替えもせず、decode surface上の留保として集計に残した。

## Focal control結果: blue circleとblue square

`blue_circle`と`blue_square`のいずれについても、固定115-item panelには、3つの
pairwise context（`raw`、`leading_space`、`glyph_prompt`）のどれにおいても、
7 output classすべてで次の2条件を同時に満たす単一candidateはなかった。

1. Item spanのtoken数が等しい。
2. 各tokenizer vocabularyの内側だけで比較して、先頭tokenを少なくとも1つ共有する。

8件の非glyph ASCII controlは、どちらのfocal itemについても、これらのcontextで
token数だけを全class共通に揃えるcandidateさえ提供しなかった。つまり、1つの
universal control panelを7つのtokenizer構造へそのままtransportすることはできない。

これはmatched controlが作れないという意味ではない。GPT-2、Llama、OLMo、Mistral、
Qwenのoutput class内では、多数の色・形pairが条件を満たす。一方、Gemmaでは複数の
色付きshapeが別々のatomic tokenであり、別glyphと先頭tokenを共有する条件そのものが
満たせない。したがって、outcomeを見た後に基準を弱めるのではなく、tokenizer output
classごとにmatching ruleを固定する必要がある。

## 設計上の帰結

次のactivation protocolでは、tokenizer output classごとに独立したprospective control
setを定義する。少なくとも次をfreezeする必要がある。

- 正確なinput contextとitem-span rule
- そのtokenizerで実現可能なequal-count条件とprefix条件
- Atomic-tokenの場合に使う、token数＋Unicode construction一致などのfallbackを、
  別control familyとして申告すること
- target bank、primary endpoint、hypothesis family、多重性rule
- negative cellとmatch failureをすべて残すこと

このcensusは設計空間を狭めるが、勝ったmodel、layer、emoji family、interventionを
選ばない。既存GPT-2 Milestone 2の結果も変更しない。将来tokenizerをまたぐ主張をする
場合は、別に固定したcontrolと、outcomeに依存しないtarget設計が必要である。

## 再検証

公開したcompact artifactは、tokenizerやmodelをloadせずに検証できる。

```bash
python scripts/collect_multifamily_tokenizer_census_v0.py \
  --validate-output artifacts/multifamily_tokenizer_census_v0
```

Validatorはcompact file roster全体、記録した全SHA-256、aggregateとreceiptのbinding、
collector scriptのhashを検査する。Passing receiptはintegrity evidenceであり、科学的な
確認ではない。
