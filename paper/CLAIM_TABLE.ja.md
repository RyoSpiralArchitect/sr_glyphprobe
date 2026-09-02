# 論文の主張と証拠 (v5)

[English](CLAIM_TABLE.md) | [論文README](README.ja.md)

状態: **論文だけを読んだ読者のレビュー後、論文改訂v5向けの記述を指定済み**。T19/T20の結果と判定は
すべて保つ。別途事前指定した195項目の、コサイン・マージンを測る条件付きattention経路
実験を追加する。
許可するwording、証拠denominator、除外を変える場合は、対応するmanuscript文を
変える前にversion付き更新が必要である。

| Manuscriptでの記述 | 状態と証拠 | 必須の境界 |
|---|---|---|
| Atomic emojiは、事前指定した主要4構成の少なくとも3構成で、literal codepointよりも単語の重複しないCLDR keywordをよく検索する。 | 支持: core 4/4が正、partial-conjunction `p = 0.0027`。 | 固定したT19-Lのテキスト入力、後期読み出し区間、top-1 endpointに限る。 |
| Keywordの結果は4種類の表現のトークン数を完全一致させても成立する。 | 支持: 9/9構成がunrestricted / matched componentと`0.02` floorを通過。 | 一致したのはtoken countであり、token identityやtokenizer非依存性ではない。 |
| この関係は公式short nameのexact lookupより広い。 | 事前指定endpointの範囲で支持: 正確なCLDR keywordを用い、公式名とのASCII英数字単語の重複がない。 | この単語単位の規則は、部分語・token ID・学習時の共起まで排除しない。CLDR keywordは人間評価済みの同義語・paraphraseではない。U+1F923 / lmaoは設計の具体例であり、個別項目の効果を独立に確認した例ではない。 |
| 事前指定panelではemojiのkeyword効果がsymbolのkeyword効果を上回る。 | 記述的secondary: emoji−symbolの点推定が両componentで9/9構成で正。 | emoji panelとsymbol panelはカテゴリ・頻度・ラベル品質・token identityで交換可能ではない。 |
| 公式名の検索は非emoji記号にも広がる。 | 記述的secondary: symbolの公式名効果が両componentで9/9構成でkeyword効果を上回る。 | 指定panel間の比較に限り、Unicode symbol母集団を推定しない。 |
| Rank-8のlate `attn_out` / `mlp_out` componentは必要かつ十分である。 | 不支持: 主要block-24両サイトともjoint criterionを通らず、全サイトで両成分同時通過なし。事後的な全状態交換のsufficiency効果は主要サイトで `0.0000`/`+0.0052` と登録floor未満だった。 | 登録済み判定は不変。較正は事後的かつ記述的で、負の結果はLlama 3.2 3Bの1構成・6サイト・rank 8・1 endpointに限る。 |
| Block-27 MLPが因果メカニズムである。 | 不支持: sufficiency adjusted `+0.0781` に対し necessity adjusted `-0.0156`。ポストホック複合天井 `+0.2448` 対 keyword単独 `+0.0365` がself-retrieval破壊分を定量化。 | このpatchはclean alias insertionとは記述できない。 |
| 交換介入最適化したrank-8部分空間は、late residual/componentサイトで必要かつ十分である。 | 登録評決: **両主要サイトでuncalibratable**（sufficiency天井 `+0.0234`/`+0.0254` が登録済み情報量最低値 `0.06` 未満）。副次サイトも通過なし。 | この評決は較正条件の未達を記録し、当該説を未解決のまま残す。1モデル・rank 8・読み出しトークン介入・4文脈に限る。 |
| 読み出しトークン全体の交換はblock 21/24で非対称な効果を示し、block 27では両ベースラインを再現する。 | 登録済み対照による記述的支持: necessity効果はglyphとcodepointのベースライン差の `4%`/`25%`（block 21/24）で、block 27では厳密転写（`100%`）。sufficiency効果は `71%`/`76%`。block 24 attentionの `2%` はsufficiencyを指す。 | 最終blockのresidual全体交換は、期待されるendpoint整合性確認である。それ以前の検索性能の保持は回復仮説を動機づけるが、経路の同定、全rankの排除、全体交換がすべての部分空間介入の上界であることは示さない。小さいcomponent効果から情報の不在も言えない。 |
| T21が、冗長な符号化によってT20の交換非対称性を説明した。 | 未確立。T20は384項目のtop-1、T21は別の195項目の条件付きコサイン・マージン効果を測る。 | 非対称性は狙いを絞った経路仮説を動機づける。T21の肯定結果はその条件付き寄与を支持するが、冗長な符号化の証明や、先行する非対称性の完全な説明ではない。 |
| T20の訓練過程では改善がある一方、保留項目の成績は限られる。 | 訓練履歴の記述的証拠: residualサイトの後期ミニバッチInfoNCEは低下する一方、source validationは`0--1`項目。評価のadjusted sufficiencyは最大`+0.0046`（`p = 0.0085`、補正前の成分検定）で`0.02` floorの4分の1未満。 | 各seed内ではvalidationが最大となる最初の時点を、seed間では最大値・同点なら小さいseedを採用する。600ステップ目のミニバッチ損失は採用基底の測定ではない。訓練量、項目固有の符号化、最適化の限界を区別できない。 |
| Matched randomizationの帰無期待値は`1/n`である。 | 一般には成立しない。`1/n`は残したgallery全体からの一様な当て推量の基準である。 | 対応をstratum内で置換するので、予測先が対象のstratum内にあるときだけ帰無の正答確率`1/stratum_size`が生じる。codepoint項は固定する。 |
| T21のマージン変化だけで自項目のkeywordコサインの変化が確立する。 | マージンは二項を含む。位置対照との差の両平均を事後分解すると、自項目への正の変化（`+0.002428`/`+0.004402`）が最大競合への変化（`+0.000103`/`+0.002135`）に部分的に相殺されていた。 | 全195項目と元の5対比を保つ。成分の追加検定を伴わない記述的平均である。最大競合は変わり得るため、独立したmediatorの同定や確認判定の変更はしない。 |
| T19 matched emojiの数は31–41項目である。 | Gemmaの51を含む**31–51**へ訂正する。元の予測配列の形状と計算は正しかった。 | 36検定・区間をコンパクトな再計算で確認し、元の項目数や判定を変えない。主要`p=0.0027`も不変。 |
| コードポイント表記の読み出し状態への置換後、glyph位置からの後段attentionは、同数の接尾位置対照を上回って対応語のコサイン・マージンに寄与する。 | 事前指定した195項目、Llama 3.2 3Bのblock 21で支持。五つすべての片側・同時95%下限が正。位置対照との差は低下`0.002326`・回復`0.002267`、下限`0.001399`・`0.001400`。 | 未使用項目を再構成する前に384項目の探索で候補を選択。距離8の二文脈と固定集団の二ドナーを項目内で平均。条件付き介入・マージン指標・1モデル・近似的項目bootstrapに限り、絵文字固有性や唯一の回路は主張しない。 |
| T21-Cは検索正答率や行動的steeringの改善を示す。 | 不支持。単語top-1の平均効果は絶対的低下・絶対的回復・位置対照との差の回復で0、位置対照との差の低下は`-0.001282`。保存済み条件別平均による主要条件の置換後基準正答率はpipe `3.08%`、article-a `0.51%`（block 21、距離8、全195項目）。 | 低い基準正答率で低下が捉えにくい可能性はあるが、床効果による説明は未確立。この平均は同等性や全項目の不変性を示さない。生成や下流の行動は未評価。T19/T20の判定も不変。 |
| モデルはemojiを視覚的に知覚する、または人間的に意味を理解する。 | 除外。 | 入力はtext-onlyのUnicode scalarであり、raster知覚・行動的理解のテストは実施していない。 |
| この結果は普遍的なemoji manifold、完全なcircuit、scale law、モデル母集団効果を同定する。 | 除外。 | 9 cellは固定された交絡ありrosterで、因果テストは1モデルのみ。 |
| T19/T20はpretraining novelty或いはtokenizer非依存性を確立する。 | 除外。 | Emoji表面は過去実験やpretrainingに出現し得る。確立したのはsymbolのrepository-text freshness、因果バンクのT19/T20-forward freshness、token-count matchingのみ。 |

## Controlling sentence

> Raw atomic emojiは、4種類の表現のトークン数を完全一致させた解析でも、
> 事前指定した9つのモデル・トークナイザ構成で、literal codepointよりも
> 単語の重複しないCLDR keywordをよく検索する。T19-CとT20-Cは、試したrank-8の
> 読み出しトークン仮説を支持しなかった。最適化部分空間の追試は、登録済み規則の下で
> 両主要サイトの評価がuncalibratableとなった。全状態交換では深さ依存の非対称性が
> 見られた。別途事前指定した195項目のattention経路実験は、対応語のコサイン・マージン
> への条件付き寄与を確認した。glyph情報の絶対的な置換・復元による平均top-1効果は0だった。
