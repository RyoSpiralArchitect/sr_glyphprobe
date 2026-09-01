# T18 論文ストーリー：未提示表層から語彙へ

[English](PAPER_STORY_T18_FRESH_LEXICAL_V0.md) · [T18結果](FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0_RESULTS.ja.md) · [T18 protocol](FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0.ja.md) · [T17までのストーリー](PAPER_STORY_T17_GLYPH_NAME_V0.ja.md)

状態：**Workshop論文の背骨候補。Manuscript全体のclaim tableはまだfreezeしていない**。

## 仮タイトル

> **From Codepoints to Names: Fresh-Surface Lexical Binding of Composite Emoji in Language Models**

## 一文で言うと

研究内で未提示だった192件の複数コードポイント絵文字を事前固定して調べたところ、
生Unicode列はliteral codepoint列より標準英語短名をよく検索し、この差はtoken数を
完全一致させても4つのcore model/tokenizer cellすべてで残った。しかし、立ち上がる深さ、
global geometry、対応できるitemの顔ぶれはmodelごとに違った。

論文の中心は、この一文で十分に立つ。主張を狭く保ったまま、内部表現の面白い不均一性まで
含んでいる。

## なぜ「glyphの問い」へ綺麗に戻れたのか

出発点は、絵文字や記号がmodel内部に固有の指紋を残すか、という問いだった。T16では、
Unicode列の長さや順序、構成だけでもhidden stateが大きく動くと分かった。意味を語るには、
構造対照を厳しくしなければならない。T17ではraw emojiから短名への広い対応が見えたが、
対象はT9/T10ですでに開いていた。

T18は、そこに足りなかった確認gateを埋めた。

1. Tokenizerを見る前に、新しいraw surfaceを選ぶ。
2. T11の全identityを除外する。
3. T17だけを根拠に後期windowを決め、T18 activationを見る前にfreezeする。
4. Unrestrictedとtoken数完全一致の両方を必須にする。
5. 同じcore cellが、統計条件と実用下限を同時に満たすようにする。
6. Repo露出監査と18本のrandomizationを、別実装で再計算する。

したがって結論は「modelが絵文字の絵を見た」ではない。Text modelが、標準化された
複数コードポイント列をどのように語彙へ結び付けるか、という診断結果である。

## 経験的な三層

### 1. 集約効果は確認できた

Core 4 cellはすべて通過し、partial conjunctionは`p = 0.0001`。9 cell全体でも8 cellが
統計＋実用ruleを満たした。ここが確認的な中心になる。

### 2. 多言語とtoken構造の境界が見えた

日本語短名でも9 / 9 modelが正方向だった。日本語専用のtoken数一致層でも同じである。
ただし、日本語は二次解析であり、意味の言語非依存性を示さない。Token数対照は有力な
代替説明を一つ落としたが、token identityやbyte経路までは揃えていない。

### 3. 集約は共通でも、中身はmodel固有だった

Paired item marginは9 / 9で短名を支持したが、matched CKAは3 / 9のみ。4 coreすべてで
正だったitemは192件中8件で、item-effect相関は`0.0245`〜`0.2035`にとどまった。
一つの共通emoji manifoldを見つけたのではない。異なるitem rosterと深度trajectoryから、
似た集約効果が立ち上がっている。

## 既存研究との違い

- [emoji2vec](https://aclanthology.org/W16-6208/)は、説明文から絵文字embeddingを学習する。
  T18は既学習modelを診断し、生Unicode列、固定label、codepoint表記を比較する。
- [ELCo](https://aclanthology.org/2024.lrec-main.1381/)は、複数絵文字からなるphraseの
  行動的な合成を扱う。T18は、標準上は一つのgrapheme clusterとなる複数コードポイント列を、
  一件ずつhidden-state geometryで調べる。
- [What Do Tokens Know About Their Characters and How Do They Know It?](https://aclanthology.org/2022.naacl-main.179/)
  はsubword tokenの綴り情報をprobeする。T18が見るのは、生Unicode列と標準語彙labelの
  item-specificな対応で、literal encodingを対照に置く。
- [Assessing Emoji Use in Modern Text Processing Tools](https://aclanthology.org/2021.acl-long.110/)
  はNLP tool全般の絵文字処理を広く評価する。T18は、固定したmulti-model設計の中で、
  一つの内部表現関係だけを切り出す。

Populationとlabelは、版を固定した[Unicode Emoji 17](https://www.unicode.org/Public/17.0.0/emoji/emoji-test.txt)と
[CLDR JSON 48.2.0](https://github.com/unicode-org/cldr-json/tree/48.2.0)から作った。

## 論文の組み立て案

1. **問いと脅威モデル**：raw surface、語彙label、literal encodingは別物。描画知覚は対象外。
2. **Prospective population**：exact-surface freshnessを説明し、事前学習holdoutとは分ける。
3. **凍結実験**：9 cell、系統等重み、後期window、token数層、IUT、partial conjunction、実用下限。
4. **一次結果**：core 4 cellと独立再計算を先に示し、その後9 cell全体を載せる。
5. **どう実装されているか**：深度の不均一、CKAとの分離、日本語二次結果、item共有の疎らさ。
6. **境界**：T16のUnicode構造対照、tokenizer限界、学習系譜の共有、視覚・因果claimなし。
7. **次の一手**：正式label対paraphrase、非emoji記号対照、その後に別freezeの因果局在。

T15の行動・steering結果は研究program全体の導入には使える。ただしT18の主張と本文の中心を
奪わせない。T16は主に脅威モデルか補遺に置き、なぜ語彙対応という狭い読み方が必要なのかを
支える役にする。

## Figure案

- **Figure 1**：raw emoji、英語・日本語短名、codepoint literalと、未提示表層の監査境界。
- **Figure 2**：9 modelのunrestricted / matched後期差と`0.02`実用下限。
- **Figure 3**：全深度trajectory。共通相転移ではなくpeakの不揃いを見せる。
- **Figure 4**：paired margin対CKAの符号と、core item-overlap matrix。
- **補遺**：系統別profile、日本語専用match、Qwen記述列、token coverage、全receipt。

## Manuscript freeze前のclaim table

| 候補claim | 現在の状態 | 境界 |
|---|---|---|
| 未提示raw emojiは、4 core中3以上でcodepoint literalより英語短名をよく検索する | 支持 | 登録済み後期windowとmodel cell内 |
| Token数完全一致でも残る | 支持 | token identityやtokenizer非依存性ではない |
| 日本語labelも同じ向き | 記述9 / 9 | 日本語の事前登録推論なし |
| 共通の後期相転移がある | 非支持 | peakとonsetが違う |
| 一つのglobal emoji-name manifoldがある | 非支持 | matched CKAは3 / 9 |
| 同じ絵文字が全modelを駆動する | 非支持 | core全共通は8 / 192 |
| Modelが絵文字を視覚認識・意味理解する | 許可しない | text-codepoint inputのみ |
| Parameter数とともに効果が増える | 許可しない | Qwen列は交絡した記述値 |
| 因果的な語彙回路を同定した | 未実施 | 新しいfreezeと未使用bankが必要 |

## 次に最も効く実験

単純に絵文字数を増やすのではなく、語彙controlを交差させる。

```text
raw emoji
  × 正式短名
  × 事前選定paraphraseまたはalias
  × 日本語label
  × literal codepoint列
  × 名前を持つ非emoji Unicode記号
```

正式table名のlookupと、より広い語彙近傍への対応を分ける小さな一次contrastを先にfreezeする。
それを通過してから、新しい未使用評価bank上で、後期`attn_out` / `mlp_out`の
除去・追加・復元を比較する。Consensus itemとmodel-private itemは層として使えるが、T18の
結果を見て唯一の因果siteを選ぶことはしない。

## 書き方の境界

使う表現は「exact-surface-fresh」「repository-relative」「lexical binding」
「item-specific retrieval」。避けるのは「modelにとって未見」「視覚的glyph認識」
「意味理解」「universal」「scale law」「9 modelの独立replication」である。
