# Glyph-System Reserve Confirmation v0 結果（T12）

[English](GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.md) · [凍結済みプロトコル](GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0.ja.md) · [コンパクト証拠](../artifacts/glyph_system_reserve_confirmation_v0/README.ja.md) · [T11探索atlas](GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.ja.md) · [次の問いの設計図](EMOJI_STEERING_SPECIFICITY_ATLAS_V0.ja.md)

状態: **一度限りの確認実験を完了。登録した2仮説はいずれも確認されなかった**。

T12では、これまで一度もforwardしていなかったZWJ 96件とregional flag 64件の
reserveを、全件まとめて一度だけ開いた。取得前に凍結した2つの仮説を、9つの
model/tokenizer cell、2種類のcarrier、4つの距離で検定した。
`H_ZWJ_FUSION`も`H_REGIONAL_DUAL`も確認されなかった。結果を見た後にendpoint、
実用床、model gate、多重性の規則を変更していない。

今回の負の結果は、単に「何も起きなかった」という内容ではない。Regionalの
presentation/fusionは9モデル中8モデルで正方向を示し、component単独の未補正
p値も`0.03538`だった。ただし全体統計量は`0.002767`にとどまり、事前に定めた
実用床`0.02`を大きく下回った。Regionalのcomponent trackingはさらに小さく、
棄却にも至らなかった。ZWJ presentation/fusionは未補正の統計境界に近かった
（`p = 0.05496`）ものの、統計量は`0.000369`で、実用床`0.005`には届かなかった。
したがって、方向が揃っているという事実だけでは、どちらの登録仮説も救済できない。

これは「モデルに絵文字表現がない」という結果ではない。T11で見つけた特定の
分解候補が、未使用reserveにおいて、事前指定した大きさとmodel横断の一貫性では
再現しなかった、という結果である。

## 取得と来歴

修正後の凍結commitは
`ab64488dc4bd28510c353f4370cda5546bb34750`、manifestのSHA-256は
`38046552a26bef0eb6cdab3222f58041707616028fe89c0eb5104a84f0943738`である。
Tokenizer/artifact preflightではmodel weightを読み込まず、reserve forwardも0回に
保った。AggregateのSHA-256は
`3a51837c6c6a149b88e05db2528b5ebd2437d50c89e8ffdcfaaee1a343bc8ee1`である。

凍結した9 roleはすべて完走した。

- Llama 3.2 3B base
- Qwen 2.5 baseの0.5B、1.5B、3B、7B
- OLMo 2 1B base
- Gemma 2 2B instruction-tuned
- SmolLM2 1.7B base
- Mistral 7B Instruct v0.3

各roleは160件すべてを10 shardで取得し、固有のmodel forward 1,088回と、
returned-finalのFP32 readout vector 4,352本を記録した。Joint acquisition全体では、
90 shard、model forward 9,792回、vector 39,168本である。Interventionとgenerationは
どちらも0回。Raw activationはGitにもSpiralShareにも置いていない。

Endpointは厳密に`output.hidden_states[-1]`であり、実装がfinal normalizationを持つ
場合は、その後にmodel APIが返すfinal hidden stateとして扱った。T12では
raw-last-blockも中間depthも保存していないため、別endpointによる救済はできない。

## Tokenization対照

Primaryのwrong-label比較はすべて、同じglyph systemとtokenizerの中で、targetの
token数を完全に一致させた。登録cell全体でrequired control coverageの最小値は
`0.979167`で、凍結済みgateの`0.75`を上回った。さらに厳しい感度分析では、targetの
先頭tokenも一致させた。Coverageの最小値は`0.729167`で、凍結済みgate`0.70`を
上回った。

Strict-prefix感度は、ZWJでは9モデルすべて、regional presentation/fusionでは
9モデル中8モデル、regional componentでは9モデル中6モデルで正方向だった。
ただしこれは必須gateであっても、primary control、実用床、異質性rule、Holm判定の
失敗を救済しないよう、あらかじめ定めていた。

## 登録済み判定

Primary統計量は、72個のmodel × context item中央値の中央値である。各elementary
testでは、glyphとdecompositionをitem内で共有して入れ替えるrandomizationを
49,999回行った。Regional仮説はintersection-unionのAND条件なので、2 componentの
p値の大きい方を仮説p値とした。登録仮説2件をfamilywise alpha `0.05`のHolm法で
補正した。

| 登録component | 全体統計量 | 正のcell | 正のmodel summary | 実用床に達したmodel | 未補正p |
|---|---:|---:|---:|---:|---:|
| ZWJ presentation/fusion | 0.000369 | 50/72 | 6/9 | 0/9（床0.005） | 0.05496 |
| Regional presentation/fusion | 0.002767 | 53/72 | 8/9 | 0/9（床0.02） | 0.03538 |
| Regional component tracking | 0.000666 | 41/72 | 5/9 | 0/9（床0.02） | 0.12950 |

| 登録仮説 | 結合方法 | 仮説の未補正p | Holm補正p | 確認 |
|---|---|---:|---:|---|
| `H_ZWJ_FUSION` | elementary test 1件 | 0.05496 | 0.10992 | なし |
| `H_REGIONAL_DUAL` | regional 2 componentのp値の最大 | 0.12950 | 0.12950 | なし |

3つのelementary testはすべて、全体の実用床と「9モデル中6モデル以上が実用床に
達する」という条件に不合格だった。負の実用床まで反対方向へ進んだmodelはなく、
strict-prefixの方向gateはすべて通った。したがって今回の不合格は、小さい効果量、
model単位での実用的支持の不足、そしてZWJとregional component trackingでは
未補正でも棄却しなかったことの組合せである。符号反転が支配した結果ではない。

## 探索から確認で何が変わったか

対応するT11 discovery中央値は、ZWJ presentation/fusionが`0.0142`、regional
presentation/fusionが`0.0668`、regional component trackingが`0.0441`だった。
T12 reserveでは、それぞれ`0.000369`、`0.002767`、`0.000666`となった。この差そのものに
別のdiscovery対reserve検定を与えたわけではないが、T11候補が探索時の大きさでは
移送しなかったことは明瞭である。

これは、一度限りのreserveが検出するために用意されていた選択圧そのものである。
T11は探索atlasとして引き続き有用だが、T12によって、その強い分解patternを
「modelをまたいで確認済みの現象」へ格上げすることは防がれた。

## 独立検証と公開証拠

独立validatorはT12のacquisition/analyzer moduleをimportしない。Freeze、preflight、
9本のrun receipt、9本のshard indexを再hashし、保存済み432 cell中央値をすべて再構築した。
さらに49,999回のrandomization 3件と、実用床、異質性、strict-prefix、
intersection-union、Holmの全判定を再計算し、不一致は0件だった。

ただし、これは独立したmodel replicationではない。コンパクトbundleはraw FP32
activation arrayを含まないため、activationからitem contrastを作る段階はhashで拘束する
だけで、再構築していない。したがって評価は「留保付きで共有可能」とする。

Git内の証拠は次のコマンドで検証できる。

```bash
python scripts/validate_glyph_system_reserve_confirmation_v0_result.py \
  validate-public-bundle \
  --bundle artifacts/glyph_system_reserve_confirmation_v0
```

Primary resultのSHA-256は
`1dee4bd187c5816d809cec27c4972edb217442e7824ef172a7d5933557d491a6`である。

## 主張境界と次の問い

T12が閉じるのは、このreserve questionだけである。絵文字の意味、理解、因果性、
mechanism、behavioral steering、tokenizer非依存性、scale law、instruction tuning効果、
architectureやmodelへの一般化、独立再現は確立しない。T10を変更も救済もしない。

次に行うべきなのは、reserve結果から都合のよいlayerやendpointを探すことではない。
元の広い問いへ戻ることである。絵文字由来の介入には、意味を揃えたword direction、
tokenizationを揃えた非絵文字Unicode、rare-token対照、normを揃えたrandom directionを
越えて残る現象があるのか。[T13の設計図](EMOJI_STEERING_SPECIFICITY_ATLAS_V0.ja.md)では、
新しいtarget bank、intervention endpoint、多重性familyを別に凍結するまで、この
future workを探索として扱う。
