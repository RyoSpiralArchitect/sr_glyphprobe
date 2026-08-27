# Multifamily tokenizer census v0

[English](MULTIFAMILY_TOKENIZER_CENSUS_V0.md) · [研究ロードマップ](ROADMAP.ja.md) · [科学的契約](SCIENTIFIC_CONTRACT.ja.md)

プロトコルID: `glyphprobe-multifamily-tokenizer-census-v0`

## 位置づけと目的

これは、この115-item censusのlive出力を見る前に用意した、tokenizer
構造だけを対象とする固定censusである。この英日文書、固定panelとconfig、audit
scriptとtest、checksum manifestを含む最初の公開commitで、実行条件のfreezeが
有効になる。

既存のGPT-2向け絵文字controlを複数のtokenizer familyへ移したとき、token数と
token prefixの構造がどこまで残るか、またUnicodeの合成がその構造をどう変えるかを
調べる。これはcontrol設計の準備であり、activation実験でもbehavior実験でもない。

## 固定する問い

正の結果を得るためのgateは設けず、次の4点を記述する。

1. **Tokenizer間のfragmentation:** 固定文字列ごとのraw token数が、固定rosterの
   tokenizer間でどの程度変わるか。
2. **Prefix controlの候補:** raw、先頭space付き、glyph-plus-promptの各surfaceで、
   token数が等しく、各tokenizer内で先頭1または2 tokenを共有するitem pairはどれか。
3. **合成による増分:** skin-tone、variation selector、keycap、ZWJ sequenceの
   token数が、固定baseまたは固定componentのtoken数合計からどの程度変わるか。
4. **Wrapper感度:** 同じitemを単体、先頭space付き、marker wrapper内、固定prompt
   `probe`の前に置いたとき、itemと重なるtoken spanが変わるか。

これらからcontrol候補や交絡候補は得られるが、意味、表現、機構、因果効果は識別できない。

## 固定panel

順序を固定したpanelは、重複のない115文字列からなる。

- 既存E1のsky、food、animals、transport、socialの5 blockから、単一code point
  50件
- `blue_circle`と`blue_square`を含む、既存の色付きcircle/square 10件
- hand/skin-toneのbaseとsequence 8件
- 固定したZWJ component 16件とZWJ sequence 8件
- regional indicatorによるflag 4件
- U+FE0Fを含むtext/emoji presentation pair 7件
- keycapのbase/sequence 4件
- 絵文字でないASCII control 8件

正確な順序と関係は、
[`multifamily_tokenizer_sequences_v0.yaml`](../data/emoji_panels/multifamily_tokenizer_sequences_v0.yaml)、
configが参照する既存panel 6件、freeze manifestで固定する。Live出力を見た後に、
itemの追加、削除、改名、並べ替え、置換をしてはならない。Panelを変える場合は、
新しいprotocol versionを作る。

Family名は報告用のstratumであり、このcensusが検証する意味labelではない。見た目が
1つの絵文字でも、複数code point、variation selector、zero-width joiner、regional
indicatorを含み得るため、auditでは正確なcode point列とUTF-8 byte列を残す。

## 固定するtokenization surface

すべてのtokenizerで、`local_files_only=true`、`use_fast=true`、
`trust_remote_code=false`、`add_special_tokens=false`を使う。各itemを次の4 templateで
auditする。

| Context ID | Template |
|---|---|
| `raw` | `{item}` |
| `leading_space` | ` {item}` |
| `marker_wrapper` | `Marker: {item} ->` |
| `glyph_prompt` | `{item}\nprobe` |

Fast tokenizerのoffset mappingで、itemと重なるtoken spanを定義する。各rowにはtoken
ID、token piece、offset、span位置、decode結果、round tripの成否、code point、
UTF-8 byteを残す。Token IDを比較するのは、同じtokenizer vocabularyの内側だけである。

## Availabilityに基づく固定roster

このcensusの出力を見る前に、3 nodeへすでに存在したtokenizer artifactからrosterを
選んだ。量子化modelと非量子化modelが同じtokenizer assetを共有することはあるが、
model名から同一性を仮定せず、実際のlocal fileをhashする。

| Node | 固定tokenizer label |
|---|---|
| `mac1` | `mac1_llama32_3b`, `mac1_mistral7b_instruct_v03`, `mac1_gpt2`, `mac1_gemma4_e4b_it`, `mac1_olmo3_7b` |
| `mac2` | `mac2_llama32_3b_bf16`, `mac2_mistral7b_instruct_v03_4bit`, `mac2_gemma2_2b_4bit`, `mac2_qwen25_3b`, `mac2_gpt2` |
| `furnace` | `furnace_gemma2_2b_it`, `furnace_gemma3_4b_it`, `furnace_gemma3_12b_it`, `furnace_mistral7b_instruct_v03` |

各labelは必ずnode receiptに残す。Loadまたは互換性のfailureもfailure rowとして保持し、
結果を見た後に別tokenizerへ差し替える根拠にはしない。FurnaceのLlama 3 8BとGemma 2
baseは、完全なlocal tokenizer snapshotがなかったためfreeze前に除外した。このprotocolは
それらをdownloadしない。

## 固定する記述output

Tokenizer (m)、item (i)、context (c)について、itemとoffsetが重なるtoken数を
(n_{m,i,c})とする。Censusでは次を公開する。

- 全tokenization row
- family別のraw token数histogram
- 成功したroster entry間における、各itemのraw token数の最小値、最大値、range
- base delta (n_{m,i,raw}-n_{m,b(i),raw})
- component-sum gap
  (n_{m,i,raw}-\sum_{j\in components(i)}n_{m,j,raw})
- 固定したpairwise contextについて、token数一致、prefix共有、tokenizer内の完全な
  token列一致を含む、すべての順序なしitem pair

6,555 pairをすべて保持する。Candidateのfilterは完全なtableを作った後だけに行い、
都合の悪いpairを削除できない。Token数一致、prefix共有、token列一致は構造上の観測で
あり、意味の同等性を示さない。

## 実行とfailureの規則

選択したnode rosterの各labelについて、`--tokenizer LABEL=LOCAL_PATH`を1件ずつ渡す。
指定labelの集合はrosterと完全一致しなければならない。Outputは同じ親directoryにある
hidden staging directoryへ書き、最後に1回のrenameで公開する。Output directoryには
次を置く。

- `tokenizations.jsonl`
- `pairwise_controls.jsonl`
- `summary.json`
- `receipt.json`
- `SHA256SUMS`

Receiptにはtokenizer/config/script asset、package/runtime identity、成功・failureの全row、
outputの件数とhash、model forward callとprotected target accessが0であることを記録する。
1 tokenizerのfailureで他labelのrowを消してはならない。すべてのtokenizerが失敗した場合も、
failed receiptを含むbundleを公開し、commandはnonzeroを返す。一部のroster entryだけが
失敗した場合も、complete-with-failures bundleを保持したままnonzeroで表面化する。

## 保護inputと主張の境界

Scriptはtarget case、source wrapper、model weight、activation、logit、behaviorを読まない。
特に、使用済みP2 confirmatory bankとretired C1 bankは、open、sample、tokenize、その他の
どの方法でもinspectしてはならない。

許される最も強い表現は、**事前指定したlocal利用可能tokenizer rosterのうち成功した
memberを対象に、固定115文字列のtokenization構造を記述した**、である。

このcensusはMilestone 2を更新せず、Llama 3.2 3Bのnegative bridgeを救済せず、因果layerを
選ばず、tokenizer非依存の絵文字構造を確立せず、Phase I論文gateも満たさない。後続の
activation cellではtokenizer構造を測定済みcovariate/controlとして保持し、その結果を見る
前に別protocolとして固定する。
