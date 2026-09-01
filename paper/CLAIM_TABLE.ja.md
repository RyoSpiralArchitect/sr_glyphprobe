# 凍結済みmanuscript claim table (v1)

[English](CLAIM_TABLE.md) | [論文README](README.ja.md)

状態: **manuscript draft v1向けに凍結済み**（T20-C結果の着地を受けてv0を更新）。
許可するwording、証拠denominator、除外を変える場合は、対応するmanuscript文を
変える前にversion付き更新が必要である。

| Manuscriptでの記述 | 状態と証拠 | 必須の境界 |
|---|---|---|
| Atomic emojiは、凍結core cellの少なくとも4件中3件で、literal codepointより語彙的に非重複なCLDR keyword aliasをよくretrieveする。 | 支持: core 4/4が正、partial-conjunction `p = 0.0027`。 | 固定したT19-L text入力、late-window readout、top-1 endpointに限る。 |
| Alias resultは4 viewのtoken countを完全一致させても成立する。 | 支持: 9/9 cellがunrestricted / matched componentと`0.02` floorを通過。 | 一致したのはtoken countであり、token identityやtokenizer非依存性ではない。 |
| この関係は公式short nameのexact lookupより広い。 | 凍結endpointの範囲で支持: aliasはcanonical-name wordとASCII-alphanumeric wordが非重複なexact CLDR keyword。 | CLDR keywordは人間評価済みの同義語・paraphraseではなく、pretrainingに含まれ得る。 |
| 凍結panelにおいてemojiのalias効果はsymbolのalias効果を上回る。 | 記述的secondary: emoji−symbolの点推定が両componentで9/9正。 | emoji panelとsymbol panelはカテゴリ・頻度・ラベル品質・token identityで交換可能ではない。 |
| Official-name retrievalはemoji限定の現象より広い。 | 記述的secondary: symbolのcanonical効果が両componentで9/9、alias効果を上回る。 | 凍結panel間の比較であり、Unicode symbol母集団の推定ではない。 |
| Rank-8のlate `attn_out` / `mlp_out` componentは必要かつ十分である。 | 不支持: 主要block-24両サイトともjoint criterionを通らず、全サイトで両成分同時通過なし。ポストホックのfull-interchange天井は主要サイトで `0.0000`/`+0.0052` — 登録floorが到達可能効果を上回っていた。 | 登録済み判定は不変。天井較正はpost-hocかつ記述的。否定はLlama 3.2 3Bの1 cell・6サイト・rank 8・1 endpointに限る。 |
| Block-27 MLPが因果メカニズムである。 | 不支持: sufficiency adjusted `+0.0781` に対し necessity adjusted `-0.0156`。ポストホック複合天井 `+0.2448` 対 keyword単独 `+0.0365` がself-retrieval破壊分を定量化。 | このpatchはclean alias insertionとは記述できない。 |
| 交換介入最適化したrank-8部分空間は、late residual/componentサイトで必要かつ十分である。 | 登録評決: **両主要サイトでuncalibratable**（sufficiency天井 `+0.0234`/`+0.0254` が登録済み情報量最低値 `0.06` 未満）。副次サイトも通過なし。 | この評決は当該説の証拠ではなく、「このendpointは登録判定を載せられなかった」ことの記録。1モデル・rank 8・読み出しトークン介入・4文脈に限る。 |
| 最終状態のkeyword信号はblock 21--24の読み出しトークン残差ストリームには担われず、glyph位置文脈から再構成される。 | 登録済み天井による記述的支持: full-swap necessity天井は到達可能量の `4%`/`25%`（block 21/24）に対し block 27 で厳密転写（`100%`）。sufficiency天井は `71%`/`76%`。 | 天井は登録済みの記述的統制であり判定endpointではない。主張はこのcell・このretrieval endpoint・読み出しトークン単一位置swapに限る。 |
| 最適化rank-8部分空間はsource項目を記憶するが共有担体を見つけない。 | 記述的支持: 訓練InfoNCEはresidualサイトで `0.52--1.26` まで低下する一方、source保留validationは `0--1` 項目のまま。新鮮バンクでのadjusted sufficiencyは最大 `+0.0046`（`p = 0.0085`）でfloorの1桁下。 | 訓練は96項目。汎化ゼロはitem-private符号化とも訓練データ不足とも整合する。 |
| モデルはemojiを視覚的に知覚する、または人間的に意味を理解する。 | 除外。 | 入力はtext-onlyのUnicode scalarであり、raster知覚・行動的理解のテストは実施していない。 |
| この結果は普遍的なemoji manifold、完全なcircuit、scale law、モデル母集団効果を同定する。 | 除外。 | 9 cellは固定された交絡ありrosterで、因果テストは1モデルのみ。 |
| T19/T20はpretraining novelty或いはtokenizer非依存性を確立する。 | 除外。 | Emoji表面は過去実験やpretrainingに出現し得る。確立したのはsymbolのrepository-text freshness、因果バンクのT19/T20-forward freshness、token-count matchingのみ。 |

## Controlling sentence

> Raw atomic emojiは、exact four-view token-count matchingの下で、9つの凍結
> model/tokenizer cellにわたり、literal codepointよりも語彙非重複なCLDR keyword
> aliasをよくretrieveする。一方、1モデルにおける2つの事前登録因果実験は、late
> readout-token subspace説をどの構成でも支持しない — 閉形式rank-8テストは
> ポストホック天井がほぼゼロのサイトでjoint criterionを外し、較正付き
> 最適化部分空間follow-upは主要サイトでuncalibratableと登録され、その
> full-interchange天井は到達可能な信号を最終ブロック群とglyph位置文脈に
> 局在させる。
