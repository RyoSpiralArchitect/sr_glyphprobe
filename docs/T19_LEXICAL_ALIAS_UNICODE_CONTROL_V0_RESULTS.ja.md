# T19 語彙エイリアス × Unicode 記号対照：結果

[English](T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0_RESULTS.md) · [凍結protocol](T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.ja.md) · [論文ストーリー](PAPER_STORY_T19_LEXICAL_NEIGHBORHOOD_V0.ja.md)

状態: **T19-L の登録済みprimaryは陽性、T19-Cの登録済みprimaryは陰性**。

## 一段落でまとめると

凍結した九つのmodel/tokenizer cellすべてで、atomic emojiをそのまま入力した表現は、
正式名と語彙的に重ならないCLDR keyword aliasを、literalなcodepoint表記よりよく
取り出した。Unrestrictedと、四つのviewのtoken数を完全一致させたmatched解析の
両方で、9/9 cellがmodel IUTと`0.02`の実用下限を通過した。四つのcore cellを使う
登録済みpartial conjunctionは4/4陽性、`p = 0.0027`だった。非emoji Unicode記号の
alias効果は小さく不均一で、emoji-minus-symbolの点推定は両componentとも9/9で正だったが、
この比較はsecondaryである。続く因果実験は未使用のemoji 192項目で完走した。
六つのzero hookとrestorationはすべて厳密に一致した一方、primaryであるblock 24の
二siteは必要性と十分性の積集合を通らなかった。T19が支持するのは、token数を揃えても
残るemojiとCLDR語彙の広い対応であり、固定rank 8の単純な後半component因果説明は棄却された。

## 凍結と証拠

- 実行凍結commit: `eec6f36261b2d2ee243c2404586eedc8e71adef1`
- Freeze SHA-256: `5dbbe0ef746cc3a002b8916de647a1c16a1e9f76a3f31fd4a0b53966f9c212fc`
- Selection SHA-256: `7a51d38effe67e74ff1264ae61c652e4192088063c3d31c874421f0b4dad8ee2`
- 観察analysis receipt: `1ebf8795c20463f2cff7b2ac5ff045aecaaeda2d8ddabc878822d6182b47e817`
- 観察独立validation: `afefacfeb75e8aeeb5bdfff34b4202f10f552087040177b81d2de5f405701b46`
- Causal go manifest: `1ac8d331f0ca2c40e9888857cd379d5c745f78a85c9c333fe33e7760cdba3df2`
- Causal source receipt: `f57f03bd97dcb9e2ebd8b8dda601a3351879e1a028abb471b94a2353678c2961`
- Causal evaluation receipt: `b519fd04ba307c61ec4d0b81b93b051669444f66e40d5c03b5a32463adfb0166`
- Causal analysis receipt: `cfd1983cdee843af6c00ea4b2a2c94eed5b34118631a6698c02c035d98855fa1`
- 因果独立validation: `dac9d28b74305b4db5536879961024470e4a4efbf29e527210b2662b93713355`

観察実験は7,920 model forward、285,120 readout vector、45 sealed shardを使った。
因果実験はsource 256 forward、evaluation 2,880 forward、8,064 intervention rowである。
Raw arrayはfurnaceのscratchに置き、Gitには含めていない。

## T19-L primary result

統計量は、観察用emoji 55項目について24 contextで平均した
`top1(glyph → alias) − top1(glyph → codepoint)`である。`U`はunrestricted、
`M`はglyph、正式名、alias、codepoint literalのtoken数を完全一致させた解析を表す。

| 凍結cell | U効果 | M効果 | Model IUT p | 陽性 |
|---|---:|---:|---:|:---:|
| Qwen 2.5 0.5B base | +0.0364 | +0.0702 | 0.00055 | yes |
| OLMo 2 1B base | +0.0652 | +0.0712 | 0.00135 | yes |
| Qwen 2.5 1.5B base | +0.0530 | +0.0631 | 0.00185 | yes |
| SmolLM2 1.7B base | +0.0606 | +0.0528 | 0.00005 | yes |
| Gemma 2 2B IT | +0.0886 | +0.0825 | 0.00005 | yes |
| Llama 3.2 3B base | +0.0856 | +0.1075 | 0.00135 | yes |
| Qwen 2.5 3B base | +0.0712 | +0.0833 | 0.00005 | yes |
| Qwen 2.5 7B base | +0.1818 | +0.1869 | 0.00005 | yes |
| Mistral 7B Instruct v0.3 | +0.2386 | +0.2577 | 0.00005 | yes |

Core cellはLlama 3.2 3B、Qwen 2.5 7B、OLMo 2 1B、Gemma 2 2Bの四つで、
すべて陽性だった。三番目に小さいcore IUT p値は`0.00135`で、登録済みの
`r = 3 of 4` Bonferroni partial conjunctionは`2 × 0.00135 = 0.0027`となった。
必要だった三cellに対して、実際には四cellが通過した。

独立validatorは、sealed prediction arrayからkind × componentの36 randomization testを
再構築し、45 raw shardを再hashした。全summary/run bindingも検証し、同じgate判定を得た。

## 正式短名だけの対応だったのか

Alias endpointは、CLDR正式短名と語彙的に重ならないよう事前に選んだ。それでも
codepoint endpointを9/9 cellで上回った。したがって、T18が見ていたものを
「一つの正式label文字列だけを取り出す現象」とする狭い説明では足りない。

ただし、これは同義語理解を示さない。Aliasは人手評価したparaphraseではなく、
CLDRのkeywordそのものである。学習dataの中でemojiや正式名と並んでいた可能性もある。
モデル平均のemoji alias-minus-codepointはunrestrictedで`+0.0979`、matchedで
`+0.1084`。正式名の平均効果はそれより大きく、`+0.1440`と`+0.1718`だった。
平均的には正式名の方が強いkeyであり続けた。

深度profileはsecondaryである。全modelとcontextで平均したunrestricted emoji alias効果は、
最初のblockの`+0.0409`から正規化深度`.875`の`+0.1152`へ上がり、最終的に
`+0.0922`となった。一方、個別modelのpeakは最初のblock、`.75`、`.875`、`1.0`に
分かれ、共通のonsetやpeakはなかった。

## 非emoji Unicode記号対照

55記号は、凍結したrepository text境界に現れない、1 scalarの非emoji Unicode記号である。
Alias効果は不均一だった。

- symbol alias-minus-codepointのmodel平均はunrestricted `+0.0236`、matched `+0.0153`。
- Qwen 2.5 3Bと7Bは、symbolの両componentで負だった。
- emoji-minus-symbolの点推定は、unrestrictedとmatchedの両方で9/9 cellが正だった。
- symbolでは、正式名retrievalがalias retrievalを両componentの9/9 cellで上回った。

これらは登録済みsecondary resultである。正式名retrievalはemojiだけの現象ではないが、
語彙的に離れたCLDR keywordまでの広がりは、凍結したemoji panelで大きいことを示唆する。
ただし、label品質、学習頻度、token identity、記号category、視覚的な馴染みは揃っていない。
Emoji固有の意味能力を示す結果ではない。

## T19-C 因果結果

128 source emojiから、固定した各siteでrank 8のglyph–alias cross-covariance部分空間を学び、
別の192 emojiへ介入した。必要性は、学習部分空間を除いた効果とsource-span内のrandom
部分空間を除いた効果の差である。十分性は、glyph-to-codepoint patchと同型random patchの差である。

| Site | Primary | 調整済み必要性 | p | 調整済み十分性 | p | Engineering | IUT p |
|---|:---:|---:|---:|---:|---:|:---:|---:|
| `attn_out` block 21 | no | -0.00521 | 1.00000 | +0.00521 | 0.49983 | pass | 1.00000 |
| `mlp_out` block 21 | no | +0.00000 | 1.00000 | +0.00521 | 0.49760 | pass | 1.00000 |
| `attn_out` block 24 | yes | +0.00000 | 1.00000 | -0.00521 | 1.00000 | pass | 1.00000 |
| `mlp_out` block 24 | yes | +0.00521 | 0.49989 | +0.00000 | 0.74912 | pass | 0.74912 |
| `attn_out` block 27 | no | +0.00000 | 1.00000 | +0.01042 | 0.31511 | pass | 1.00000 |
| `mlp_out` block 27 | no | -0.01562 | 0.96895 | +0.07812 | 0.00009 | pass | 0.96895 |

Zero hookとrestorationの最終state RMSは、六siteすべてで厳密に0だった。したがって、
primary陰性はengineering gateの失敗ではない。Block 24では、どちらのcomponentも
`0.02`の効果・下限条件に届かなかった。

Secondaryのblock 27 `mlp_out`十分性は、次の仮説を考える手掛かりにはなるが、
陽性の因果siteではない。調整済み効果は`+0.07812`、片側`p = 0.00009`、item bootstrap
95%下限は`+0.03646`だった。一方、必要性は逆向きの`-0.01562`、`p = 0.96895`で、
凍結IUTは不合格となった。さらに十分性endpointの内訳は、alias top-1が`0.0052`から
`0.0208`へ上がると同時に、codepoint自己retrievalが`1.0000`から`0.9375`へ下がっている。
純粋なalias挿入とは呼べない。

独立因果validatorはsource/evaluation arrayを再hashし、12 sign-flip test、12 bootstrap
interval、部分空間の直交性、全bindingを再計算した。Engineeringは6/6通過、primary陽性siteは0だった。

## 解釈

T19は、説明の余地を二方向から狭めた。

1. Raw emojiとの対応は、一つの正式短名を越えて、語彙的に重ならないCLDR keywordまで
   九つの凍結cellすべてで広がり、token数を完全一致させても残った。
2. その対応は、登録した単純な機構では説明できなかった。Sourceから学んだrank 8部分空間は、
   block 24の`attn_out`と`mlp_out`のどちらでも、未使用itemに対して必要かつ十分ではなかった。

分散的、冗長、非線形、item-privateな実装とは整合するが、T19だけでは区別できない。
また、因果陰性の範囲は一model、一rank、一carrier/distance、二primary site、一つの
final-hidden retrieval endpointに限られる。

## 主張境界

許されるのは、九つの凍結model/tokenizer cellにおけるtoken数一致の語彙対応と、
Llama 3.2 3Bで登録したrank 8 component介入の陰性結果までである。描画glyphの知覚、
人間的意味、同義語理解、pretraining novelty、tokenizer非依存性、普遍的emoji manifold、
唯一または完全な回路、model母集団への一般化、instruction tuning効果、scale lawは示していない。
