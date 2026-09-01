# 凍結済み初稿claim table

[English](CLAIM_TABLE.md) | [論文README](README.ja.md)

状態: **manuscript draft v0向けに凍結済み**。許可するwording、証拠denominator、
除外を変える場合は、対応するmanuscript文を変える前にversion付き更新が必要である。

| Manuscriptでの記述 | 状態と証拠 | 必須の境界 |
|---|---|---|
| Atomic emojiは、凍結core cellの少なくとも4件中3件で、literal codepointより語彙的に非重複なCLDR keyword aliasをよくretrieveする。 | 支持: core 4/4が正、partial-conjunction `p = 0.0027`。 | 固定したT19-L text入力、late-window readout、top-1 endpointに限る。 |
| Alias resultは4 viewのtoken countを完全一致させても成立する。 | 支持: 9/9 cellがunrestricted / matched componentと`0.02` floorを通過。 | 一致したのはtoken countであり、token identityやtokenizer非依存性ではない。 |
| この関係は公式short nameのexact lookupより広い。 | 凍結endpointの範囲で支持: aliasはcanonical-name wordとASCII-alphanumeric wordが非重複なexact CLDR keyword。 | CLDR keywordは人間評価済みの同義語・paraphraseではなく、pretrainingに含まれ得る。 |
| 凍結panelではemoji alias effectがsymbol alias effectを上回る。 | 記述的secondary: emoji-minus-symbol point estimateは両componentで9/9が正。 | emoji / symbol panelはcategory、frequency、label quality、token identityでexchangeableではない。 |
| Official-name retrievalはemojiだけに限定されない。 | 記述的secondary: symbol canonical effectは両componentでsymbol alias effectを9/9上回る。 | 凍結panel比較であり、Unicode symbol母集団の推定ではない。 |
| Rank-8の後期`attn_out`または`mlp_out` componentはjointに必要かつ十分である。 | 非支持: primary block-24 siteはいずれも不通過で、両componentを通過したsiteはゼロ。 | 陰性結果は一つのLlama 3.2 3B cell、6 site、rank 8、一つのendpointに限定。 |
| Block-27 MLPが因果mechanismである。 | 非支持: sufficiency adjusted `+0.0781`に対しnecessity adjusted `-0.0156`、secondary IUT `p = 0.96895`。 | Patchはcodepoint self-retrievalも一部下げるため、cleanなalias insertionとは呼べない。 |
| Modelはemojiを視覚的に知覚し、人間のように意味を理解する。 | 除外。 | 入力はtext-only Unicode scalarで、raster知覚もbehavioralな理解testも行っていない。 |
| 普遍emoji manifold、完全な回路、scale law、model母集団effectを特定した。 | 除外。 | 9 cellは固定されたconfounded rosterであり、因果testは一つのmodelだけである。 |
| T19はpretraining noveltyまたはtokenizer非依存性を示す。 | 除外。 | Emoji surfaceは以前の実験やpretrainingに現れ得る。成立するのはsymbolのrepository-text freshnessとtoken-count matchingだけ。 |

## 統制文

> Raw atomic emojiは、4 viewのtoken countを完全一致させた9つの凍結済み
> model/tokenizer cellで、literal codepointより語彙的に非重複なCLDR keyword
> aliasをよくretrieveした。一方、一つのmodelで事前登録したrank-8の後期
> component interventionでは、そのreadoutにjointに必要かつ十分なprimary siteは
> 見つからなかった。
