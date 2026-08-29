# Glyph-System Decomposition Atlas v0 結果（T11）

[English](GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.md) · [凍結protocol](GLYPH_SYSTEM_DECOMPOSITION_V0.ja.md) · [compact evidence](../artifacts/glyph_system_decomposition_v0/README.ja.md) · [T10結果](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.ja.md)

状態：**探索的discovery atlasとして完了。留保付き共有可能**。

今回の結果を、単一の「絵文字意味軸」として読むのは無理がある。Token長を揃えた対照の後にもglyphと名前の対応は広く残ったが、その分かれ方はglyph systemとmodel cellによって異なる。Regional flagでは、whole-sequenceの名前との関係とcomponentとの関係が最も明瞭に併存した。ZWJ sequenceでは、公式のwhole-sequence nameよりcomponent labelへ同等以上に寄りながら、融合形には小さいが安定した優位がある。Modifierではmatched alignment自体は広く見える一方、三つのdecomposition contrastはいずれもほぼゼロだった。Keycapはdiscoveryが8件しかなく、変動が大きい。

これは確認的な結果ではなく、探索atlasである。絵文字の意味や理解、因果、機構、behaviorとの関係、tokenizer非依存性、scale law、instruction tuning効果、architecture一般性、model一般性、独立再現は、いずれも確立していない。T10の救済や改訂にも使わない。

## 取得と検証

Protocolはcommit `1602749815cf8007588024f89497cc5646de9f54`で凍結した。Outcomeに依存しないprotocol coreのSHA-256は`5ef2e31e7bd04f079426d84db1f3437ee2d6278ff47f587826943a5101324f94`である。Modelをloadする前に、9件すべてのtokenizer/artifact preflightを完了した。Aggregate preflightのSHA-256は`16484d7fa3504ddfdd9ffefc441d3270f506dc485728b7655a5ee9c2f3c8d2ff`。

固定した9 model/tokenizer cellは、それぞれ53 shard、8,174 unique forwardを完了した。取得量は次のとおりである。

- 取得対象843件、利用可能なitem-view pair 4,087組
- 完了shard 477件
- model forward 73,566回
- broad readout 588,528本、depth readout 393,984本、合計982,512本のFP32 vector
- intervention 0回、generation 0回

共同解析で追加したmodel forwardはゼロ。Reserve 268件にもmodel forwardを行っておらず、model outcomeは未観測のままである。Source analysis ledgerのSHA-256は`8f03aa191715c96ee980fe47e9a51f85ea651c4d619d9c46af345815ea6ca07a`。

独立validatorはT11 analyzerをimportせず、analysis、preflight、9件のsummary bundleを再hashした。そのうえで、保存済みitem-marginのcell中央値32,736件、model pair agreement 720行、釣り合った三要因分散分解7件、depth trajectory 2,592行を再計算した。Tolerance `1e-12`で不一致はゼロだった。

一方、model横断activation geometryはhashとschemaまで確認したが、raw vectorからは再構築していない。再計算には、Gitへ入れていない約9.15 GiBのactivation archiveが必要になるためである。Depth tableに使ったintervalはすべて照合したものの、item bootstrap全体の再標本化も独立には繰り返していない。したがって、検証判定は「独立再現」ではなく「留保付き共有可能」とした。

## 必須のtoken長matched controlは全cellで通過

Wrong-label controlは、target token数が完全に一致する層の中だけで作った。9 tokenizerを通した必須coverageの最小値は、keycap Unicode名の`0.8750`。複数のsystem/viewでは`1.0000`に達した。凍結した下限`0.75`は、すべての必須cellで満たしている。

Sensitivityでは、targetの先頭token IDも揃えた。このcoverageにはgateを置いておらず、system間の偏りが大きい。中央値はatomic anchorで`0.1406`、presentation sequenceで`0.1938`、modifierで`0.7240`、ZWJの各viewで`0.8711`〜`0.8789`、regional flagで`0.9938`〜`1.0000`、keycapで`0.8750`だった。したがって、ZWJとregional flagでは有力な感度分析になるが、anchorとpresentationでは検出力が低い。

Returned final stateでは、必須control後のglyph→公式名advantageのcell中央値が、主要4 systemのmodel×context 72 cellすべてで正だった。

| Glyph system | 項目数 | Cell中央値の中央値 | 正のcell | 記述的intervalが正 |
|---|---:|---:|---:|---:|
| Atomic anchor | 64 | 0.1134 | 72/72 | 55/72 |
| Presentation | 160 | 0.1327 | 72/72 | 71/72 |
| Modifier | 192 | 0.0548 | 72/72 | 64/72 |
| ZWJ | 256 | 0.0778 | 72/72 | 70/72 |
| Regional flag | 160 | 0.1141 | 72/72 | 64/72 |
| Keycap | 8 | 0.0909 | 65/72 | 24/72 |

先頭tokenまで揃えると、glyph/name advantageの中央値はpresentationで`0.0313`、modifierで`0.0119`、ZWJで`0.0507`まで小さくなった。それでもZWJでは68/72 cellの記述的intervalが正だった。Regional flagは中央値`0.1141`を保ち、66/72 cellでintervalが正となった。少なくともZWJとregional flagについては、target token数または先頭target tokenだけでpattern全体を説明することは難しい。ただし、これでtokenizer非依存性が成立するわけではない。Coverageの低いpresentationとanchorのsensitivityも強く読まない。

## 分解の仕方はsystemごとに違う

三つの操作的contrastは、いずれも正しいlabelとtoken長matched wrong labelとの差を土台にする。正の値は、次を表す。

- `lexicalization`：glyph→公式名がglyph→component名を上回る
- `presentation_or_fusion`：glyph→公式名がdecomposed form→公式名を上回る
- `component_tracking`：decomposed form→component名がglyph→component名を上回る

Returned final stateでのcell分布は次のとおりだった。

| System | Contrast | 中央値 | 正のcell | Interval + / − / 0を含む |
|---|---|---:|---:|---:|
| Presentation | presentation/fusion | 0.0139 | 52/72 | 25 / 3 / 44 |
| Presentation | component tracking | -0.0051 | 28/72 | 2 / 17 / 53 |
| Modifier | lexicalization | 0.0005 | 37/72 | 6 / 2 / 64 |
| Modifier | presentation/fusion | -0.0010 | 32/72 | 2 / 1 / 69 |
| Modifier | component tracking | 0.0003 | 37/72 | 9 / 4 / 59 |
| ZWJ | lexicalization | -0.0127 | 23/72 | 2 / 9 / 61 |
| ZWJ | presentation/fusion | 0.0142 | 65/72 | 31 / 0 / 41 |
| ZWJ | component tracking | -0.0040 | 26/72 | 4 / 9 / 59 |
| Regional flag | lexicalization | 0.0495 | 47/72 | 35 / 11 / 26 |
| Regional flag | presentation/fusion | 0.0668 | 59/72 | 43 / 0 / 29 |
| Regional flag | component tracking | 0.0441 | 58/72 | 36 / 3 / 33 |
| Keycap | lexicalization | 0.0030 | 38/72 | 1 / 2 / 69 |
| Keycap | presentation/fusion | -0.0090 | 33/72 | 10 / 6 / 56 |
| Keycap | component tracking | -0.0399 | 28/72 | 7 / 7 / 58 |

Presentation sequenceでは、公式名とcomponent名が構成上同一である。そのため`lexicalization`は情報を持たず、表から外した。ここで読めるのは、VS15/VS16を除いた同じscalar sequenceとfully-qualified formとの差である。`presentation_or_fusion`には小さな正の値が出たが、`component_tracking`はわずかに負だった。

Modifierの公式名とcomponent labelは、区切り文字こそ違うものの、ほぼ同じ語彙を含む。三つのcontrastはいずれもゼロ付近に集まった。これはdecomposition contrastのbounded nullであり、glyph/name matched alignment自体のnullではない。

ZWJでは、融合glyphがspace区切りのdecomposed formよりも公式名へ少し強く対応した。一方、`lexicalization`と`component_tracking`はわずかに負である。したがって、「公式のwhole-sequence nameが一般に優勢」とまとめるより、component-label affinityの上にfusion-sensitiveな関係が重なっている、と読む方が正確である。

Regional flagは、二つの構造が最も明瞭に併存した。融合flagはASCII二文字のdecomposed formやcomponent labelより公式の地名へ寄り、ASCII二文字は融合flagよりletter component labelへ寄った。ただし方向はmodel cellによって変わる。System固有の候補であり、model一般のsemantic resultではない。

Keycapのdiscovery itemは8件しかない。範囲が広く、intervalの多くがゼロを含むため、安定した分解patternは主張できない。Tag flag 3件もbounded microcaseのままで、matched-control claimを持たない。

## Poolingよりmodel-conditioned regimeが支配的

Returned-finalのmatched glyph/name marginにはmodelとsystemの主効果が見えるが、三つのdecomposition contrastはinteractionに大きく支配されていた。釣り合った総平方和に占める割合は次のとおりである。

| Metric | Model | System | Context | Model × system | Model × context | System × context | 三要因 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Matched glyph/name | 26.1% | 19.3% | 2.2% | 19.9% | 9.8% | 2.5% | 20.3% |
| Lexicalization | 2.7% | 3.5% | 1.4% | 27.4% | 10.4% | 4.1% | 50.5% |
| Presentation/fusion | 10.2% | 21.5% | 1.2% | 20.4% | 9.1% | 3.8% | 33.8% |
| Component tracking | 5.2% | 15.0% | 0.2% | 34.9% | 7.8% | 5.7% | 31.2% |

これはrandom-effects inferenceではなく、記述的な平方和分解である。それでも、「compositionalかlexicalizedか」を一つのpool値で決めると、主要な差を消してしまうことはわかる。

どのitemでmatched marginが大きいかについても、model間の一致は低い。36 model pairのSpearmanを各contextで取り、その8 contextの中央値をさらに求めると、presentationは`0.0786`、modifierは`0.0670`、ZWJは`0.1185`、regional flagは`0.1158`、keycapは`0.0089`だった。

View単体のgeometryはcross-view mappingより共有され、text viewはglyph viewより共有されていた。Returned final stateでのmodel横断glyph CKA中央値は、presentation `0.1809`、modifier `0.2018`、ZWJ `0.3645`、regional flag `0.1941`。公式名では、それぞれ`0.3594`、`0.3826`、`0.5347`、`0.4059`だった。Glyph側でmodel差が大きいというT10-Dの記述的観察は、T11でも続いている。Modelのsemantic contentを順位づける結果ではない。

Qwen base 4 checkpointのsize順に36本のsystem×metric profileを並べても、狭義単調増加は8本だけだった。Scale lawは主張しない。

## Depthとfinal normalization境界

Embedding readoutがゼロになるのは構成上の結果である。どのviewにも同じcarrier tokenを続けており、文脈混合前はreadout位置が同一だからだ。Matched glyph/nameのintervalが最初にゼロを外れた位置は、quarter-depthでpresentation 31/72、modifier 15/72、ZWJ 15/72、regional flag 17/72だった。六つのdepth readout全体では、最初に正方向へゼロを外れたtrajectoryがpresentation 54/72、modifier 33/72、ZWJ 63/72、regional flag 60/72。Architecture間で正規化したdepth上の記述であり、mechanistic siteではない。

Depth subsetにおけるreturned-final minus raw-last-blockの中央値は、glyph/name marginでpresentation `+0.0077`、modifier `-0.0021`、ZWJ `+0.0012`、regional flag `+0.0016`だった。Contrastのdeltaも、poolするとほぼゼロである。個々のmodel/system cellでは両方向に動くが、T11から一つのfinal-normalization効果は導けない。

## Retrievalは分析可能な広がりを持つが、集中も残る

Returned final stateにおけるglyph→名前のforward top-1中央値は、presentation `0.0813`、modifier `0.0365`、ZWJ `0.0488`、regional flag `0.0813`。Retrieval breadth中央値は順に`0.4437`、`0.3958`、`0.3438`、`0.4375`、top-decile concentration中央値は`0.5062`、`0.5677`、`0.6465`、`0.4938`だった。

したがって、一つの名前へ全queryがcollapseしただけではない。ただし、特にZWJでは集中が強く残る。Minimum top-1はT11の判定指標ではなく、T10の改訂にも使えない。

## 着地点と、次に切るべき一点

唯一の決定版となるlanding patternは選ばない。今回のatlasでは、次が併存している。

1. Token数matched control後にも広く残るglyph/name alignment
2. ZWJのfusion-sensitive candidate
3. Regional flagにおけるwhole-sequenceとcomponentの二重構造候補
4. Item-level agreementの弱いmodel-conditioned regime
5. Modifierとkeycapにおけるbounded decomposition null

T12を一つの問いへ絞るなら、もっとも絞りやすい候補は、returned final hidden stateにおけるZWJの`presentation_or_fusion` contrastである。Discoveryでは65/72 cellが正で、記述的intervalが厳密に負となったcellはゼロ。9 model中8 modelで8 context中央値が正となり、6 modelでは8 contextすべてが正だった。ZWJ reserveは96件ある。

ただし、この観察だけではT12は凍結されない。Reserveへforwardする前に、対象model-cell family、実用下限、context rule、multiplicity手順、必須controlとstrict-prefix sensitivity、model heterogeneityの扱いを固定する必要がある。Regional flagのcomponent trackingは有力なsecondary optionだが、ZWJと同じfamilyへ入れれば検定範囲が広がる。併合するかどうかは、意識的に決めるべき設計判断である。

## 再現と監査

返却済みcompact analysis、9件のsummary directory、tokenizer preflight directoryがある場合は、次のコマンドで独立compact validationを再実行できる。

```bash
python scripts/validate_glyph_system_decomposition_v0_result.py \
  --analysis path/to/t11-analysis \
  --summaries-root path/to/t11-summaries \
  --preflight path/to/t11-preflight \
  --output path/to/new-independent-validation
```

Gitに収録したcompact bundleだけの検査は、外部データなしで実行できる。

```bash
python scripts/package_glyph_system_decomposition_v0_public_bundle.py validate \
  --bundle artifacts/glyph_system_decomposition_v0
```

Public manifestは、収録した全file、省略した三つのcompact table、9件のsummary bundle、9件のrun receipt、preflightをhashで結ぶ。Hashはprovenanceを固定するが、省略したraw activationそのものを復元するものではない。
