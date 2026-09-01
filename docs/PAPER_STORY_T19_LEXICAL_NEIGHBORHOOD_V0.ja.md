# T19 論文ストーリー：広い語彙readoutと、単純な後半mediatorの不在

[English](PAPER_STORY_T19_LEXICAL_NEIGHBORHOOD_V0.md) · [T19結果](T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0_RESULTS.ja.md) · [凍結protocol](T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.ja.md) · [T18までのストーリー](PAPER_STORY_T18_FRESH_LEXICAL_V0.ja.md)

状態: **Phase I論文の中心候補。manuscript claim tableはまだ凍結していない**。

## タイトル候補

> **Beyond Short Names: Cross-Model Emoji Lexical Neighborhoods Without a Simple Late-Layer Mediator**

## 一文で言う貢献

Atomic emojiは、語彙的に重ならないCLDR keyword aliasをliteral codepointよりよく
取り出し、その差は四viewのtoken数を完全一致させても九つの凍結model/tokenizer cell
すべてで残った。一方、未使用emoji 192項目に対する事前登録済みrank 8の
`attn_out`/`mlp_out`介入では、必要かつ十分なprimary siteは見つからなかった。

観察の陽性と因果の陰性を、一つの結果として扱う。この論文は「emojiには意味vectorがある」
という話ではない。広く再現する語彙readoutは存在するが、最も単純な疎な後半component説明は
通らない、という制御されたdissociationである。

## T19がT18のストーリーをどう変えるか

T18では、repository上で未使用だった複合emojiが、codepoint literalより正式短名をよく
取り出すことを確認した。それでも「標準化された一つのlabel文字列を再発見しただけ」という
説明は残っていた。T19はendpointを、正式名と語彙的に重ならないCLDR keywordへ置き換えた。
Unrestrictedとtoken数一致の両解析で、九cellすべてが陽性だった。対応はofficial-label lookup
より広い。

新しいsymbol controlは、次の主張を狭く保つ。正式名retrievalは多くの非emoji Unicode記号にも
あるため、「emojiだけがwordになる」は強すぎる。一方、aliasへの広がりは凍結symbol panelで
かなり小さく、emoji-minus-symbolの点推定は九cellすべてで正だった。これはspecificityの手掛かりであり、
emojiだけの能力を登録済み推論で証明したものではない。

## 結果の三層

### 1. 確認された語彙の広がり

`r = 3 of 4`のcore primaryは`p = 0.0027`で通過し、coreは4/4陽性だった。
さらに九cellすべてがtokenizationの両componentと実用下限を通った。独立実装は36本の
randomization testとrawからsummaryまでの証拠chainを再構築した。

これが論文で最も強い新しい主張である。固定した文字列入力とretrieval endpointの下で、
atomic emojiは一つの正式名だけでなく、より広い語彙近傍のkeyになる。

### 2. 範囲を限定したemoji–symbol dissociation

モデル平均では、emojiのalias効果はsymbol平均の約4〜7倍だった。倍率はcomponentによって変わる。
正式名は、とくにsymbolでaliasより強かった。観察結果は次のような段階を示す。

```text
正式名retrieval
    emojiとnamed symbolに広く現れる

語彙的に離れたkeyword retrieval
    凍結emoji cellでは頑健
    symbolでは小さく、modelごとに不均一
```

Symbol category、頻度、label品質、token identityを完全には揃えていない。したがって、これは
独立したsemantic claimではなく、論文の境界結果として扱う。

### 3. 単純なmechanism testの陰性

T19-Cでは、別の128項目をsource bank、192項目をevaluation bankにした。六siteすべてで
zero hookとrestorationは厳密に一致した。それでもprimaryのblock 24 `attn_out`と
`mlp_out`は不合格だった。調整済み必要性・十分性効果はほぼ0で、実用下限もIUTも通らなかった。

Secondaryのblock 27 MLPは、不完全だからこそ示唆的である。学習patchはrandom patchより
endpointを動かしたが、学習座標を除いても悪化しなかった。座標はendpointを動かせても、
必須mediatorではない。分散的・非線形な説明を考える動機にはなるが、確認結果ではない。

## 論文構成案

1. **Threat model。** Raw Unicode surface、正式label、語彙近傍、literal encoding、描画知覚を分ける。
2. **Prospective design。** CLDRの出典固定、語彙非重複、三bank、token数stratum、一つの因果admission gateを説明する。
3. **モデル横断観察primary。** Core 4/4と全体9/9を先に示し、matched coverageと独立再計算を続ける。
4. **Named-symbol境界。** 正式名とalias、emojiとsymbolのprofileを示すが、secondary比較を格上げしない。
5. **因果的反証。** 厳密なengineering control、二つのprimary陰性site、block 27 MLPの非対称なsecondaryを示す。
6. **解釈。** 読み出せるaggregateな語彙関係は、一つのshared manifoldや低rank late mediatorを意味しない。
7. **限界と次の実験。** 人手評価alias、token identity control、分散multi-site介入、非線形readout、独立model母集団。

## Figure案

- **Figure 1:** emoji/symbol × canonical/alias/codepointのcrossed designと、観察/source/evaluation bank分割。
- **Figure 2:** 九modelのunrestricted・matched emoji効果と`0.02`下限。四coreを明示する。
- **Figure 3:** emojiとsymbolのalias・canonical profile。Secondaryであることを図中に書く。
- **Figure 4:** 六siteのnecessity–sufficiency平面とengineering状態。Primaryのblock 24を強調する。
- **Appendix:** 深度trajectory、厳密token stratum、全condition metric、source/evaluation hash、独立validator。

## Manuscript freeze用claim table

| 主張候補 | 証拠 | 境界 |
|---|---|---|
| Atomic emojiは少なくとも3/4 coreでdisjoint CLDR keywordをcodepointよりよく取り出す | supported; 4/4, partial conjunction p=0.0027 | 凍結late windowとendpoint |
| 四viewの厳密token数一致後も残る | supported; 9/9が両component通過 | token identity・tokenizer非依存ではない |
| T18はofficial-label lookupだけだった | 狭い説明は弱まった | CLDR keywordが学習時に共起した可能性は残る |
| Alias breadthはsymbolよりemojiで大きい | 9/9で正の点推定 | 登録済みsecondary、control panelは完全交換可能ではない |
| Block 24 rank 8の`attn_out`または`mlp_out`が必要十分mediator | unsupported | 一つのLlama cellと一介入family |
| Block 27 MLPが因果mechanismである | unsupported | 十分性は正、必要性は負、secondaryのみ |
| Modelがemojiを視覚的・人間的に理解する | unauthorized | Unicode text inputのみ |
| 普遍的emoji manifoldやscale lawがある | unauthorized | model-private trajectoryと交絡したmodel roster |

## 次に強い実験

次はemoji panelをさらに増やすより、説明を検定する。

1. 小さなalias/paraphrase setを人手で、同義性、specificity、familiarityについて評価し、
   tokenizer outcomeを見る前に凍結する。
2. Unicode categoryと語彙頻度帯を近づけたsymbol controlを作り、token数だけでなくtoken identityも設計変数にする。
3. 凍結したlate band全体で、分散multi-site removalを試す。一site rank 8の追加探索は優先度を下げる。
4. 新しいsource/evaluation splitで、linear cross-covarianceと非線形・sparse readoutを比較する。
   T19-Cを見て勝つ方法を選ばない。
5. Block 27の非対称性を予測として凍結する。語彙関係が冗長なら、transportは可能でも必要性は出ないかもしれない。

## 書き方の境界

「lexical correspondence」「CLDR keyword neighborhood」「token-count matched」
「registered causal negative」「distributedまたはredundantの可能性」を使う。
「semantic understanding」「emoji concept vector」「visual recognition」「universal circuit」
「causal localization succeeded」「tokenizer-independent」は避ける。
