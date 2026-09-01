# T17 glyph–name 論文ストーリー v0

[English](PAPER_STORY_T17_GLYPH_NAME_V0.md) · [T17結果](GLYPH_NAME_DEPTH_TRAJECTORY_V0_RESULTS.ja.md) · [現在のPhase I構成案](PAPER_OUTLINE.ja.md) · [T16ストーリー](PAPER_STORY_T16_V0.ja.md)

状態：**投稿候補の背骨。最終的な論文claim freezeではない**。

## 仮題

**From Raw Emoji Surface to Lexical Name: A Cross-Model Depth Atlas**

別案：

1. **When Does an Emoji Become Its Name? Depth-Resolved Correspondence Across Language Models**
2. **Local Lexical Retrieval Without Global Manifold Alignment in Emoji Representations**
3. **Tracing Raw Emoji Surfaces to Unicode Names Across Decoder Depth**

最初の題が最も安全である。`Become`は印象に残る一方、表現が別物へ変換されたように読みやすい。
新しい項目集合で確認するまでは、題に`semantic`を入れない。

## 一文でいうと

固定した9つのlanguage-model cellでは、raw emoji surfaceはnetworkの中盤から後半にかけて、
codepoint識別子よりUnicode正式名を引くitem-level keyになっていく。ただし、その始まりとpeakは
modelごとに異なり、表現空間全体の整列も必要としない。

## 何が貢献になるのか

「言語モデルの中に絵文字の意味を見つけた」を先頭に置くべきではない。証拠より大きすぎるうえ、
今回きれいに測れた対象をかえって見えにくくする。貢献は、普段ひとまとめにされる三つを、
深さ方向に分けたことにある。

```text
raw Unicode surface        公式の語彙ラベル          codepoint識別子
        🐈              ↔       CAT FACE          versus      U+1F408
             item検索は収束し得る
                       それでも
            空間全体の幾何は収束しなくてよい
```

GlyphProbeが提供するのは、次の四点である。

1. Itemとcontextを固定したまま、raw surface、正式名、codepoint literalを分ける監査可能な
   paired-view benchmark
2. Exact revision、endpoint名、token数一致層、item-clustered uncertaintyを伴う、9モデル ×
   9深度のatlas
3. 局所的なitem検索とglobal CKA alignmentが分かれるという実証結果
4. 全モデル共通の後期転換や、単調なdepth・size物語は成立しないという負の構造結果

次の確認用項目でaggregateが弱くなっても、この貢献は残る。「絵文字は内部で何をするのか」という
曖昧な問いを、語彙対応、識別子幾何、tokenization、表現空間全体の形へ分け、検定できる形にしたからだ。

## Abstract草案

Emojiは人間には一つの小さな記号に見えるが、language modelにはtext tokenizerを通るUnicode文字列として
入る。そのため、内部表現の類似が語彙的な関連、codepoint identity、tokenizer構造、globalな表現幾何の
どれに由来するかは自明でない。本研究では、292個のraw emoji surfaceを、Unicode正式名とliteralな
codepoint列に対応づけ、2 carrier、4 readout distanceのもとで深さ方向に追跡する監査可能なbenchmarkを
構築した。9つのexact model/tokenizer cell、9つの正規化深度から、generationやinterventionを使わず
567,648本のhidden-state readoutを取得した。Official nameとcodepointのforward top-1差は、正規化深度
0.375以降、9モデルすべてで正だった。0.50、0.75、0.875、1.0では、item bootstrap区間の下限も
9 / 9で正となり、token数一致層の点推定は0.25以降9 / 9で正だった。一方、peakは最初のblockが
2モデル、0.125が1、0.75が1、0.875が5と分かれた。最終状態でitem-pair marginは9 / 9でnameを
支持したが、centered linear CKAは4 / 9にとどまった。Raw emoji surfaceはcodepoint識別子に比べ、
item固有の語彙ラベルを広く検索可能にするが、その経路はmodelごとに異なり、globalなmanifold alignmentも
伴わない。項目集合は先行実験ですでに開いているため、本atlasは探索的である。視覚的glyph知覚、人間のような
意味理解、tokenizer非依存性、因果は示さない。

## Evidenceの背骨

| Study | 固定したもの | 結果 | 物語での役割 |
|---|---|---|---|
| T9 | 新しい292項目reserve、Mistralの一つのreturned-final endpoint | Emojiから正式名を引く優位がcodepoint対照に対してprospectiveに通過 | 単一cellの確認anchor |
| T10 | 同じ項目とcontext、9つのexact model/tokenizer cell | 統計signalは広く見えたが、登録済みmodel横断実用ruleは不通過 | 正直なmixed最終状態境界 |
| T17-GN | 同じ最終境界に9つの正規化深度を追加 | 中後層断面は9 / 9で正、peakは不均一、marginとCKAが分離 | 機構仮説を鋭くする探索atlas |
| T16-UTF / X1 | 完全同一文字列の反復、Unicode構成、長さ、順序 | Tokenizer条件付きの構成・order幾何 | 語彙結果のheadlineではなく、交絡境界と補遺対照 |

T17でT10を遡って救済しない。T10の問いは、最終endpointで固定したmodel横断実用ruleが通るかどうかで、
答えは負だった。T17は、なぜ一つの共通thresholdが脆かったのかを問い、modelが異なる軌跡から
最終状態へ来ることを示した。

## 本文の流れ

### 1. Introduction：一つの記号に三つのidentityがある

Emojiは、人に見える記号であると同時に、Unicode文字列であり、名前を持つ語彙対象でもある。
Modelにはさらにtokenizer固有の列として入る。したがって、hidden stateの類似は複数の理由から生じる。
本文では、答えられる範囲へ問いを絞る。Raw surfaceは、いつcodepoint識別子よりUnicode正式名を
引くkeyになるのか。

### 2. Benchmark：item identityを保ち、表し方だけを変える

同じitemを3 viewで表し、carrier-distance gridも固定する。Codepoint literalはsemantic nullではない。
同じitemを指す別のsymbolic identifierである。したがってname-minus-codepointは、意味対無意味ではなく、
相対的なlexicalization contrastである。

Batch size 1、endpoint semantics、exact model revision、token数matching、20,000回のitem bootstrapを、
実装の細部ではなく研究方法として書く。

### 3. 最終状態のanchor：正のsignalと、通らなかった共通floor

新しいatlasより先にT9とT10を出す。T9は、測定が一つのheld-out Mistral cellでprospectiveに通ることを
示した。T10では正の統計成分が広がった一方、固定したmodel横断実用ruleは通らなかった。ここから、
都合のよいendpointを選び直さず、depthを説明変数として調べる理由が生まれる。

### 4. 深度atlas：行き先は近くても、道筋が違う

一つのaggregateより、9本のtrajectoryを先に見せる。`0.375`以降は全モデルの点推定が正だが、初期状態は
ほぼ0から大きな正まで広がる。5モデルは`0.875`でpeakになる一方、3モデルは`0.125`以前にpeakを迎える。
「後期に意味化する」では単純すぎる。正確なのは、**立ち上がりは不均一だが、中後層では共通して正の
断面に入る**、である。

### 5. Metricの分離：対応づけは、manifold変換ではない

Top-1とpaired marginは、各emojiが他itemではなく自分のnameへ対応するかを問う。CKAは、item間の幾何を
含む行列全体が揃うかを問う。最終状態の9 / 9対4 / 9という分離は、脚注ではなく主要結果にする。
Networkがglyph manifoldをそのままname manifoldへ回転させる、という魅力的だが強すぎる物語を防げる。

### 6. Unicode対照：headlineではなく境界

T16-UTFとT16-UTF-X1は、なぜ慎重さが必要かを示す。完全同一反復、構成family、並び順、token pathだけでも
hidden stateは動く。Main textでは短い限界として、残りは補遺に置く。Raw Unicode surfaceは純粋な視覚glyph
ではなく、lexical retrievalを「視覚意味」と呼び替えてはいけないことを示す対照である。

### 7. Discussion：atlasから次の検定へ

Atlasがあれば、最大のlayerを事後的に選ばずに次を設計できる。まず新しい項目集合で、正式名への優位がalias、
paraphrase、多言語label、tokenization matchingを越えて残るか確認する。それを通過した後に限り、共有可能な
後期windowを固定し、name情報を除去・追加・復元する。

## 図表の背骨

1. **Figure 1 — 3 view benchmark**：一つのraw emoji、正式名、codepoint literalを同じcontextに置く。
   Raster visionではなくtext-tokenizer inputだと明示する。
2. **Figure 2 — 9本のdepth trajectory**：commit済みT17 figure。Zero lineとsampled depth markerを残す。
3. **Figure 3 — Local / global dissociation**：modelごとの最終top-1またはpaired marginと、CKA差を並べる。
4. **Table 1 — Model / tokenizer roster**：exact revision、architecture、block数、一致項目数、endpoint semantics。
5. **Table 2 — Onset / peak / final**：T17結果のcompact table。Carrier × distance全cellは補遺へ送る。

紙幅が厳しければFigure 2と3を残す。T16の系列対照と全metric gridは補遺・repository evidenceでよい。

## 許される主張、許されない主張

| Claim | T17後の状態 | 論文での書き方 |
|---|---|---|
| この9 cellの中後層では、raw emojiがcodepoint literalより正式名を引きやすい | 既出population上の記述として支持 | depth、roster、uncertaintyを添えて述べる |
| Token数完全一致後も符号が残る | `0.25`以降の点推定は9 / 9で支持 | Token-count matchedであり、tokenizer-independentではない |
| 全modelに共通する後期相転移がある | 不均一な立ち上がりとpeakにより支持されない | 負の構造結果として示す |
| Item検索の一致はglobalなname manifold alignmentを意味する | 支持されない。最終CKA差は4 / 9 | Metric分離を明示する |
| Qwenは大きいほどemojiを強くlexicalizeする | 未確立 | 最終値は順序づくが軌跡は違い、sizeは交絡している |
| Modelがglyphを視覚的に知覚・理解した | 不許可 | Raw Unicode text inputに限る |
| T17はT9/T10の独立再現である | 不許可 | 既出populationの探索atlas |
| この関係は因果的である | 不許可 | 別freezeの介入まで保留 |

## 次の確認設計

Fresh populationでは、一つのraw emojiに対して、次の4 label familyをoutcome取得前に固定する。

- Unicode正式名
- 一般的なaliasまたは短いparaphrase
- 言語を事前固定した多言語名
- Literal codepoint identifier

Primary endpointは、事前に定めた共有depth windowでのofficial-name minus codepoint item retrievalとする。
Raw emoji、carrier、distance、token数一致層、model family、多重性ruleも開封前に固定する。Secondary contrastの
official name対alias、English対固定した非English labelから、Unicode table名の記憶と広い語彙associationを
分けられる。因果実験は、このgateより後ろに置く。

## 投稿時の落とし所

T17は、大きな「絵文字意味」claimよりも、表現解析としてずっと明快である。ただし、まだ探索atlasだ。
落とし所は二つある。

1. T17を中心atlasにし、新しいpopulationでの確認を最大の未完了gateとして明記する。
2. 現在のT16「行動は読めるが因果実装は未解決」を主論文に保ち、T17を、語彙対応がそのまま意味回路では
   ないことを示すcompactな表現節として入れる。

Fresh populationを開くまでは、確認の背骨が強いのは2、問いが最も澄んでいるのは1である。どちらを選ぶかは、
大きなcurveが出たかではなく、主張の明瞭さと検証の完了度で決める。
