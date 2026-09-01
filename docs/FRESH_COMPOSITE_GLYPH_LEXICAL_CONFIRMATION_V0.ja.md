# 未提示の複合glyphに対する語彙対応確認 v0

状態: **事前設計済み。freeze時点のT18 model forwardは0回**。

English companion: [FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0.md](FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0.md)

## 何を確かめるか

T17では、絵文字から英語短名を検索するとき、終盤層でコードポイント表記より高い成績が得られた。ただし、対象の292件はT9・T10ですでに使っていた。そこでT18では、問いを次の一点に絞る。

> このリポジトリがmodelに一度も提示していない絵文字表層でも、終盤層の生Unicode列は、`U+...`表記より英語のEmoji短名と強く対応するか。

調べるのは語彙との対応であり、画像として描画されたglyphの知覚ではない。「絵文字を理解した」と示す実験でもない。

## 「未提示」の範囲

未提示かどうかは、tokenizerを調べる前、T18のmodel forwardを行う前に固定する。

- 露出監査の境界は、commit `85213ea9b493682c9198eadda5e20c5e5ab2a04d`のGit tree `bc114c57fb25f9d08f12bea1bdf367002506bd67`に含まれる全1,429 blob。
- 採用するglyphのUTF-8バイト列は、そのどのblobにも出現しない。
- T11で選んだ1,111件は、discovery・reserveを問わずすべて除く。
- 対象はEmoji 13.1以前に追加された複数コードポイント列に限る。

したがって、ここで保証するのは**このリポジトリに対する、表層の完全一致単位の未提示性**である。構成要素、標準形、意味概念、短名、国名まで未学習だったとは限らない。事前学習holdoutや意味概念holdoutとは呼ばない。

## 固定した192件

内訳は次のとおり。

| glyph系統 | 件数 |
|---|---:|
| modifier列 | 64 |
| ZWJ列 | 96 |
| regional indicator flag | 32 |

skin tone modifierだけを取り除いて標準familyを定義し、1 familyにつき1表層を選ぶ。各系統では、SHA-256でfamily代表を決めたあと、subgroupを決定論的にround robinする。最終順はEmoji 17のsource index順。tokenizerの測定値は対象選択に使わない。

データ源は次の版に固定した。

- [Unicode Emoji 17 `emoji-test.txt`](https://www.unicode.org/Public/17.0.0/emoji/emoji-test.txt)、SHA-256 `1d8a944f88d7952f7ef7c5167fef3c67995bcae24543949710231b03a201acda`
- [CLDR JSON 48.2.0](https://github.com/unicode-org/cldr-json/tree/48.2.0)。英語・日本語、base・derivedの4ファイルを個別にhash固定

## 4つの表記

各項目について、重複のない4表記を用意する。

1. `glyph`: 生のUnicodeコードポイント列
2. `english_short_name`: Emoji 17のcomment name。CLDR英語`tts`との一致を必須とする
3. `japanese_short_name`: CLDR日本語`tts`
4. `codepoint_literal`: 大文字16進数を空白区切りした`U+...`列

carrierは`" a"`と`" |"`を各8回、suffix距離は`1, 2, 4, 8`。batch sizeは1。T10・T17と同じ境界検査を通し、chat templateやspecial tokenは加えない。

## 収集する深さと一次window

収集する深さは9点。

`0, .125, .25, .375, .5, .625, .75, .875, 1.0`

一次windowは`.75, .875, 1.0`に固定する。既知のT17結果では、この区間でmodelをまたいだ優位が最も安定していたためだ。T17を見て選んだwindowではあるが、T18のactivationを見る前に決めている。それ以外の深さは二次解析として残し、都合のよい深さで一次結果を置き換えない。

## 一次評価

model・深さ・carrier・距離・glyph系統ごとに、次の手順で評価する。

1. 各表記を、同じglyph系統の項目間で別々にcenterする。
2. 各行をL2 normalizeする。
3. glyphから英語短名へのforward top-1 item retrievalを計算する。
4. glyphからコードポイント表記への検索も同様に計算する。
5. 英語短名の正解率からコードポイント表記の正解率を引く。

modelごとの統計量は、3系統と、終盤24 context（3深さ × 2 carrier × 4距離）を等重みで平均した値。候補集合はglyph系統ごとに分けるため、96件あるZWJだけが件数の多さで支配することはない。

次の2 componentを、どちらも通過しなければならない。

- **unrestricted**: 固定した全項目
- **tokenization matched**: glyph系統と、`(glyph, 英語短名, codepoint literal)`のtoken数が完全一致する非singleton strataのみ

各componentでは、英語短名の対応だけを19,999回入れ替える。入れ替えは全一次contextで同期し、コードポイント側は観測値のまま固定する。p値は`(1 + exceedances) / 20,000`。model単位のp値には2 componentの大きい方を使う。観測統計量も両方が実用下限`0.02`以上でなければならない。

tokenizerだけを使った事前検査では、matched対象が全cellで144件以上残った。系統別の最小値はmodifier 51件、ZWJ 66件、flag 23件で、固定下限の合計128件・各系統20件を超えている。候補tokenizerは、T10の全参照列を完全再生した。ただし、各modelの最初のforward前に、freezeしたmodel artifact内のtokenizerでもT18列のhashが一致することを改めて必須とする。

## model横断の判定と多重性

唯一のmodel横断一次判定には、T10と同じ4 core cellを使う。

- Llama 3.2 3B base
- Qwen 2.5 7B base
- OLMo 2 1B base
- Gemma 2 2B IT

「4 cell中3 cell以上」をBonferroni partial conjunctionで検定する。p値は、model IUT p値のうち3番目に小さい値を2倍し、1を上限とする。さらに、同じ3 cell以上がそれぞれmodel IUT `p <= 0.05`と両方の実用下限を通過することを求める。統計的に通るcellと実用下限を通るcellが別々でも陽性になる余地を残さない。残る5 cellを含む9 cell familyはHolm補正付きの二次評価であり、一次判定を救済できない。

同じ項目を使い、学習data、tokenizer系譜、architecture familyも重なる。したがって、各cellを独立replicationとは数えない。

## 二次atlas

次の解析は記述目的に限り、一次結果を救済しない。

- 日本語短名との対応
- 全9深さのtrajectory
- modifier・ZWJ・regional flag別のprofile
- 英語短名と日本語短名の対応
- forward/reverse top-1、MRR、paired margin、centered linear CKA
- token数分布とmatched coverage
- Qwen size profile、実行時間、peak memory、artifact size

英語と日本語の差は、表層から語彙への対応が英語だけの命名慣行に依存するかを考える手がかりになる。ただし、日本語でも正なら、それだけで言語非依存の「意味」を示したことにはならない。

## 想定する着地

- **一次判定が正**: 固定4 core cellのうち3 cell以上で、未提示表層と英語短名の対応を確認した、と報告する。glyph知覚や理解とは呼ばない。
- **unrestrictedのみ正**: tokenizationで説明できる可能性が残る。確認結果は負として扱う。
- **英語は正、日本語は弱い**: 英語ラベルに局在した結果として報告し、多言語への移行は未解決とする。
- **英日とも正**: 多言語の語彙対応を二次的な証拠として報告する。
- **系統差が大きい**: 3系統と等重み一次評価を維持し、よく効いた系統だけを一次主張に昇格させない。
- **一次判定が負**: T17の既提示集合から一般化しなかった、境界の明確な負の結果としてatlas全体を残す。

## 実行前のgate

model forwardまでに、次を順に閉じる。

1. 公開sourceからselectionを生成し、未提示性を監査する。
2. forward 0回のdesign receiptを作る。
3. 9 cellすべてでtokenizer-only preflightを行う。
4. engineering preflightをまとめる。
5. config、code、test、英日docs、selection、tokenizer receipt、source bindingをfreezeする。
6. freeze commitを`origin/main`へpushする。
7. 炉の空きを再確認する。
8. freezeしたmodel artifactを読み込み、T18 token列のhash一致を確認してから最初のforwardへ進む。

収集量はmodel forward 13,824回、readout vector 497,664本。32件単位の完了shardは変更しない。他のGPU processを検知した場合は、次のshardに入る前にyieldする。生activationは炉のscratchに置き、Gitには加えない。

## コマンド

```bash
python scripts/fresh_composite_glyph_lexical_confirmation_v0.py audit-selection
python scripts/fresh_composite_glyph_lexical_confirmation_v0.py audit-freeze --require-pushed
python scripts/fresh_composite_glyph_lexical_confirmation_v0.py run-role \
  --model-label MODEL_ROLE --model-path MODEL_SNAPSHOT --output-root RUN_ROOT
python scripts/fresh_composite_glyph_lexical_confirmation_v0.py summarize-role \
  --model-label MODEL_ROLE --output-root RUN_ROOT --summary-root SUMMARY_ROOT
python scripts/fresh_composite_glyph_lexical_confirmation_v0.py analyze \
  --summary-root SUMMARY_ROOT --output ANALYSIS_ROOT
```

本文と実行検査に差がある場合は、YAML configとJSON freeze manifestを正とする。
