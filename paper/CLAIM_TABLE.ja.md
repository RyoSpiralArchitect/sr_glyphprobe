# 論文の主張と証拠 (v2)

[English](CLAIM_TABLE.md) | [論文README](README.ja.md)

状態: **論文改訂v2向けの記述を指定済み**。T19/T20の結果と判定はすべて保ち、
実測した交換介入の効果と、その由来についての仮説を分けた編集上の改訂である。
許可するwording、証拠denominator、除外を変える場合は、対応するmanuscript文を
変える前にversion付き更新が必要である。

| Manuscriptでの記述 | 状態と証拠 | 必須の境界 |
|---|---|---|
| Atomic emojiは、事前指定した主要4構成の少なくとも3構成で、literal codepointよりも単語の重複しないCLDR keywordをよく検索する。 | 支持: core 4/4が正、partial-conjunction `p = 0.0027`。 | 固定したT19-Lのテキスト入力、後期読み出し区間、top-1 endpointに限る。 |
| Keywordの結果は4種類の表現のトークン数を完全一致させても成立する。 | 支持: 9/9構成がunrestricted / matched componentと`0.02` floorを通過。 | 一致したのはtoken countであり、token identityやtokenizer非依存性ではない。 |
| この関係は公式short nameのexact lookupより広い。 | 事前指定endpointの範囲で支持: 正確なCLDR keywordを用い、公式名とのASCII英数字単語の重複がない。 | CLDR keywordは人間評価済みの同義語・paraphraseではなく、pretrainingに含まれ得る。 |
| 事前指定panelではemojiのkeyword効果がsymbolのkeyword効果を上回る。 | 記述的secondary: emoji−symbolの点推定が両componentで9/9構成で正。 | emoji panelとsymbol panelはカテゴリ・頻度・ラベル品質・token identityで交換可能ではない。 |
| 公式名の検索は非emoji記号にも広がる。 | 記述的secondary: symbolの公式名効果が両componentで9/9構成でkeyword効果を上回る。 | 指定panel間の比較に限り、Unicode symbol母集団を推定しない。 |
| Rank-8のlate `attn_out` / `mlp_out` componentは必要かつ十分である。 | 不支持: 主要block-24両サイトともjoint criterionを通らず、全サイトで両成分同時通過なし。事後的な全状態交換のsufficiency効果は主要サイトで `0.0000`/`+0.0052` と登録floor未満だった。 | 登録済み判定は不変。較正は事後的かつ記述的で、負の結果はLlama 3.2 3Bの1構成・6サイト・rank 8・1 endpointに限る。 |
| Block-27 MLPが因果メカニズムである。 | 不支持: sufficiency adjusted `+0.0781` に対し necessity adjusted `-0.0156`。ポストホック複合天井 `+0.2448` 対 keyword単独 `+0.0365` がself-retrieval破壊分を定量化。 | このpatchはclean alias insertionとは記述できない。 |
| 交換介入最適化したrank-8部分空間は、late residual/componentサイトで必要かつ十分である。 | 登録評決: **両主要サイトでuncalibratable**（sufficiency天井 `+0.0234`/`+0.0254` が登録済み情報量最低値 `0.06` 未満）。副次サイトも通過なし。 | この評決は較正条件の未達を記録し、当該説を未解決のまま残す。1モデル・rank 8・読み出しトークン介入・4文脈に限る。 |
| 読み出しトークン全体の交換はblock 21/24で非対称な効果を示し、block 27では両ベースラインを再現する。 | 登録済み対照による記述的支持: necessity効果はglyphとcodepointのベースライン差の `4%`/`25%`（block 21/24）で、block 27では厳密転写（`100%`）。sufficiency効果は `71%`/`76%`。 | 検索性能が保たれることは、未変更のglyph位置文脈から回復するという仮説を動機づける。経路の同定、全rankの排除、全体交換がすべての部分空間介入の上界であることは示さない。 |
| 試した最適化rank-8部分空間はsource項目に適合し、保留項目への汎化は弱かった。 | 記述的支持: 訓練InfoNCEはresidualサイトで `0.52--1.26` まで低下する一方、source保留validationは `0--1` 項目。新しい評価集合でのadjusted sufficiencyは最大 `+0.0046`（`p = 0.0085`、補正前の成分検定）で、`0.02` floorの4分の1未満。 | 訓練は96項目。弱い汎化は項目固有の符号化、訓練データ不足、最適化の限界のいずれとも整合し、共有部分空間の不存在を示さない。 |
| モデルはemojiを視覚的に知覚する、または人間的に意味を理解する。 | 除外。 | 入力はtext-onlyのUnicode scalarであり、raster知覚・行動的理解のテストは実施していない。 |
| この結果は普遍的なemoji manifold、完全なcircuit、scale law、モデル母集団効果を同定する。 | 除外。 | 9 cellは固定された交絡ありrosterで、因果テストは1モデルのみ。 |
| T19/T20はpretraining novelty或いはtokenizer非依存性を確立する。 | 除外。 | Emoji表面は過去実験やpretrainingに出現し得る。確立したのはsymbolのrepository-text freshness、因果バンクのT19/T20-forward freshness、token-count matchingのみ。 |

## Controlling sentence

> Raw atomic emojiは、4種類の表現のトークン数を完全一致させた解析でも、
> 事前指定した9つのモデル・トークナイザ構成で、literal codepointよりも
> 単語の重複しないCLDR keywordをよく検索する。二つの因果実験は、試したrank-8の
> 読み出しトークン仮説を支持しなかった。最適化部分空間の追試は、登録済み規則の下で
> 両主要サイトの評価がuncalibratableとなった。全状態交換で見られた深さ依存の
> 非対称性は、glyph位置の文脈から回復する経路を直接検証する動機となる。
