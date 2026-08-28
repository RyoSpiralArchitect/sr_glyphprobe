# Mistral 7B semantic atlas v0

[English](MISTRAL7B_SEMANTIC_ATLAS_V0.md) · [T7結果](MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.ja.md) · [ロードマップ](ROADMAP.ja.md)

状態: **T8モデルforward前の探索的取得freeze**。この文書が定義するのは
再利用可能な観測データセットであり、確認的な意味endpointではない。

## なぜこの取得を行うか

T7は固定した1モデルintersection-union testを通過した。しかし5 familyは
Unicode上の連続blockであり、固定Mistral tokenizerでは50 glyph中49件が、ほぼ
「共通prefix・block/family token・block内token」に分解される。したがって
matched-slot recurrenceには、それだけで十分になり得るtoken構造上の説明が
残っている。同じ50件のslotを貼り替える操作はT7のfamily内同期permutation
nullそのもので、新しい対照にはならない。

T8では規模と観測対象を変える。標準で定義された大きなemoji母集団について
3種類の入力viewを取得し、後続解析でglyphを、人間可読な名前および恣意的な
codepoint文字列と比較できるようにする。生activation atlasは、現在の単一仮説
より意図的に豊かに残す。

## 母集団と未実行reserve

sourceは固定したUnicode Emoji 17.0 `emoji-test.txt`。tokenizer-only censusは
fully-qualifiedかつ単一codepointの1,184件をすべて保持する。この段階では
model weightをloadせず、model forwardも行わない。

既存E1 panelの50件を`calibration_prior_exposed`とする。残り1,134件は、
activationを見る前に、namespace `glyphprobe-t8-v0`と大文字codepointのSHA-256
で分割する。4で割った余り0を`reserved_unrun`、余り1–3を
`discovery_unseen`とした固定件数は次の通り。

- calibration-prior-exposed: 50件
- discovery-unseen: 842件
- reserved-unrun: 292件

今回取得するのは前二者の計892件。292件のreserveは、reserve activationを
見ずに後続の確認解析protocolをfreezeするまでmodel forwardを0件に保つ。
tokenizer-only検査はmodel forwardではなく、selection manifestにhashで固定済み。

## 固定した3 view

各取得itemには次の文字列を一つずつ持たせる。

1. 単一codepoint glyphそのもの
2. 固定sourceにあるUnicode名そのもの
3. 大文字`U+...`形式のcodepoint literal

名前viewは意味を持つ自然言語anchor、codepoint literalはitem identityを持つが
意味的には恣意的なtext comparatorである。どちらも完全なcontrolではない。
3 viewすべての正確なtoken IDと長さを保存するため、結果を見た後にtoken構造を
再構成せず、事前情報に基づく層別化やresidualizationを行える。

## 固定取得grid

modelは既にfurnace上で検証済みの12-file BF16 artifact、
`mistralai/Mistral-7B-v0.3@caa1feb0e54d415e2df31207e5f4e273e33509b1`。
gridは次の通り。

- view: glyph / Unicode名 / codepoint literal
- carrier: `" a"` 8 tokenと`" |"` 8 token
- 距離: view後のcarrier 1 / 2 / 4 / 8 token目
- `resid_post` layer: `[0, 4, 8, 12, 16, 20, 24, 28, 31]`
- 保存dtype: FP32
- axis: item × view × carrier × distance × layer × width

一意な入力列は5,352本、保存vectorは4,096次元で192,672本になる。固定した
item/view/carrier文字列の一つのcausal forwardには4距離すべてのreadout位置が
含まれる。同じ文字列を4回forwardする代わりに4位置を同時に読むため、通常の
backend数値再現性を除けばcausal inputは同一である。64列batchにより、21,408回の
冗長な単位置forwardではなく、約84回のbatched model callで取得する。

介入、sampling、生成、protected target、reserve入力は使わない。

## 競合に耐える保存

取得itemはsource順で固定し、最大32件ずつ28個の運用shardに分ける。完了shardは
FP32 `.npy`、JSONL observation、receipt、SHA-256 ledgerを持ち、atomicに公開する。
runnerはmodel load前と各shard開始前にforeign GPU compute PIDを検査する。競合が
現れた場合はmodelを解放し、hash検証済みの完了shardだけを残す。後続runは検証した
完了shardをskipして再開する。

shard境界に科学的意味はなく、outcomeに基づく選択は禁止する。finalizeには28個
すべてが必要。約3 GiBのraw atlasはGitへ入れず、Gitには固定protocolとcompactな
receipt/summaryのみを置く。

## 記述的オプションであって判定ではない

paired cross-view retrieval、glyph–nameとglyph–codepointのalignment差、centered
linear CKA、representational-distance correlation、Unicode group/subgroup近傍純度、
正確なtoken長層別などを、非判定的な固定summary候補として保存設計に含めた。
これらは後続解析を選ぶ材料にはできるが、T8のprimary endpointではなく、
discovery dataをconfirmationへ変換しない。

次の綺麗なgateはcalibration/discoveryだけでendpointと多重性familyを一つ定義して
freezeし、その後に292 reserveへ初めてmodel forwardを行うこと。それまでは、
このatlasが支えるのは探索的なemoji意味分解に限る。

## 主張境界

取得成功が示すのは、1 model・1 runtimeでprovenance固定、競合時再開可能な
activation datasetが存在すること。glyph–nameに魅力的なpatternが見えても、
それだけで意味内容、tokenizer因果、mechanism、behavior、architecture一般性、
Phase I paper gateは確立しない。負の結果とheterogeneityも同じ粒度で保持する。
