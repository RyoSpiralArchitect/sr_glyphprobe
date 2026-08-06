# E1 トークン同型な絵文字familyの探索結果

[English](EMOJI_FAMILY_EXPLORATORY_RESULTS.md) · [凍結済みプロトコル](EMOJI_FAMILY_EXPLORATORY_PROTOCOL.ja.md) · [研究ロードマップ](ROADMAP.ja.md) · [公開エビデンス](../artifacts/emoji_family_exploratory_v1/analysis/report.md)

## 位置づけ

E1は、範囲を限定した記述的探索として完了した。Commit
`0cd4e11610e42253ead9ce9aff9f0b02474a0558`で、英日プロトコル、panel、
config、tokenizer事前監査、endpoint、analyzerを5本のMLX runより先に
凍結している。固定したGPT-2のtoken列について、familyを表す中間token
だけを変えたとき、対応slotの出力fingerprint分離が5つの絵文字blockを
またいで繰り返されるかを調べた。

これはMilestone 2の確認実験でも、C1因果実験でもない。すでに探索で
使った24件のprestage targetを再利用した。E1ではP2とC1を開かず、
読み込み、tokenize、score、sample、model入力のいずれにも使っていない。

Bundle全体の公開検証: **pass**。独立validatorが公開payload 82件と5つの
role bindingを検証した。Hash mismatchとlocal absolute pathはいずれも0で、
P2/C1が固定済みE1 input surfaceの外にあるというmanifest上の宣言も
検査した。この宣言は、過去のprocess履歴を独立に完全証明するものではない。
Root manifestを含めると、公開fileは計83件である。

## 結果の要点

| 評価量 | Layer 2（primary exploratory） | Layer 4（事前指定したnegative comparator） |
|---|---:|---:|
| Family等重みのglobal specificity \(R_{\mathrm{global}}\) | 0.014752595564 [0.002875238085, 0.027439243404] | 0.014887989201 [0.003407563347, 0.019684351979] |
| 0を含むfamily-specific \(R_f\)区間 | 5 / 5 | 5 / 5 |
| 25個の平均\(M_{f\leftarrow g}\) cellの範囲 | 0.395455–0.484915 | 0.602564–0.681909 |

角括弧内は、bootstrap percentileによる95%記述区間である。p値に基づく
信頼区間や判定ではない。E1ではp値、多重性判定、同等性判定、選択規則、
確認的statusを算出していない。

\(M\)行列は、非対角のtransfer cellを含めて広く正だった。一方、
family-specificな超過量\(R\)は、それよりはるかに小さい。このパターンは、
意図的に共通化したGPT-2の第1・第3 tokenによる反復が支配的で、
within-familyの残差的な超過は小さいことを示唆する。意味上のfamily表現を
同定したわけではない。

Layer 4は、想定したnegative comparatorにはならなかった。Global \(R\)は
正で、layer 2とほぼ同じ大きさだった。したがってE1からlayer固有の効果は
主張しない。

## 固定した設計

報告用のfamily IDは、`sky`、`food`、`animals`、`transport`、`social`の
5つである。各familyは、連続する10個のUnicode scalarからなる。対応slot
\(j\)では、glyph単体のtoken列をすべて次の形に揃えた。

```text
[8582, family_middle_token, shared_slot_suffix_token]
```

Family間で変わるのは中間tokenだけである。したがって、family identityと
中間tokenは完全に交絡している。第1・第3 token IDは意図的に共有している
ため、非対角transferは共有token構造だけでも生じうる。

実行cellは次のとおりである。

- `openai-community/gpt2` revision
  `607a30d783dfa663caf39e06633721c8d4cfcd7e`
- MLX FP32、`resid_post`、layer 2・4、strength 0.05
- target内に入れ子にしたdirection seed 101 / 211 / 307
- source wrapper 16件すべてと、prestage targetの先頭24件。6 groupから各4件
- 各layerのrandom direction 2本と、exact zero-hook control
- neutral-direction、sign flip、label permutation、SAE、iso-KLは未実施

Source familyを\(f\)、prototype familyを\(g\)、targetを\(t\)とすると、
\(M_{f\leftarrow g,t}\)は、3 seedで平均したmatched-slot cosineから、対応しない
9 slotのcosine平均を引いた値である。Family-specificな超過量は次で定義した。

\[
R_{f,t}=M_{f\leftarrow f,t}-\operatorname{median}_{g\ne f}M_{f\leftarrow g,t}.
\]

Primary descriptive aggregateには、24 targetの算術平均を使う。Global値では
5 familyを等しく重み付けした。区間は、target groupで層化した20,000回の
joint bootstrapから求めた。各replicateで、データから推定する
leave-one-target-group-out prototypeをすべて作り直し、同じ再標本をfamily、
layer、endpoint、family pairの全条件で共有している。

## Family別の全結果

Family単位の区間は、両layerの全familyで0を含んだ。

### Layer 2

| Family | 平均\(R_f\) | 95%記述区間 | Target中央値（二次記述） |
|---|---:|---:|---:|
| sky | 0.008588 | [-0.014893, 0.038753] | 0.014093 |
| food | 0.023749 | [-0.014597, 0.052447] | 0.022765 |
| animals | -0.011182 | [-0.042184, 0.052737] | 0.012075 |
| transport | 0.064934 | [-0.017747, 0.086572] | 0.099840 |
| social | -0.012326 | [-0.032422, 0.028139] | -0.005395 |

### Layer 4

| Family | 平均\(R_f\) | 95%記述区間 | Target中央値（二次記述） |
|---|---:|---:|---:|
| sky | 0.029825 | [-0.018879, 0.047807] | 0.058611 |
| food | 0.023159 | [-0.007451, 0.043930] | 0.038054 |
| animals | 0.009492 | [-0.017226, 0.039138] | 0.022713 |
| transport | 0.034787 | [-0.017567, 0.059454] | 0.054501 |
| social | -0.022823 | [-0.043273, 0.003103] | -0.031843 |

## 平均transfer行列の全体

行はsource-familyのfingerprint、列はprototype familyである。対角cellが
within-family \(M\)、非対角cellが方向付きmatched-slot transferを表す。
各cellの区間とtarget単位の全行は、[解析report](../artifacts/emoji_family_exploratory_v1/analysis/report.md)
とJSONLに残している。

### Layer 2

| source \ prototype | sky | food | animals | transport | social |
|---|---:|---:|---:|---:|---:|
| sky | 0.476026 | 0.484915 | 0.450468 | 0.484103 | 0.458144 |
| food | 0.468883 | 0.482684 | 0.441429 | 0.470659 | 0.448881 |
| animals | 0.430329 | 0.443816 | 0.426832 | 0.434263 | 0.422365 |
| transport | 0.431020 | 0.434920 | 0.395455 | 0.478736 | 0.405605 |
| social | 0.442553 | 0.453080 | 0.431997 | 0.452717 | 0.435189 |

### Layer 4

| source \ prototype | sky | food | animals | transport | social |
|---|---:|---:|---:|---:|---:|
| sky | 0.659063 | 0.640399 | 0.642212 | 0.637573 | 0.613301 |
| food | 0.659563 | 0.669187 | 0.650004 | 0.669574 | 0.635669 |
| animals | 0.646314 | 0.632649 | 0.633404 | 0.633389 | 0.606434 |
| transport | 0.655011 | 0.668793 | 0.648537 | 0.681909 | 0.634021 |
| social | 0.631855 | 0.629910 | 0.619736 | 0.629083 | 0.602564 |

対角成分がrow内で常に最大になるわけではない。したがって、広く正の\(M\)
latticeが示すのは反復とtransferであり、family-specificな分離ではない。

## Random controlと不均一性

Family × layer × direction-seedの30 cellのうち、
`emoji_advantage_over_random <= 0`だったのは10 cellである。

- layer 2、seed 307: 5 familyすべて
- layer 4、seed 101: 5 familyすべて

残る20 cellから、random controlに対する頑健な優位性は主張しない。Familyを
またいで揃ったこのseed patternは、事前指定したcell単位でrandom-control比較が
不均一だったことを示す。Seedは独立観測ではなく、方向を繰り返し推定した値で
ある。

## 完全性と来歴

- 5本のrun receiptはすべて`complete`。各family 1,776 intervention row
- 全8,880 intervention rowを確認。内訳はemoji 7,200、random control 1,440、
  zero hook 240
- 全runでerror 0。Zero hookによるactivation/logit RMSの最大値はいずれも0
- 5本のreceiptに記録された実行時間の合計は321.236315秒。この値は
  マシン固有の来歴であり、MLX一般の速度結果ではない
- 公開解析gridは、family-target 240行、方向付きtransfer-target 960行、
  family summary 10行、非対角transfer summary 40行

軽量な公開エビデンスは、次の場所にまとめた。

- [E1 root manifest](../artifacts/EMOJI_FAMILY_EXPLORATORY_V1_MANIFEST.json)
- [tokenizer-only preflight](../artifacts/emoji_family_exploratory_v1/preflight/tokenization_audit_v1.json)
- [解析出力](../artifacts/emoji_family_exploratory_v1/analysis/)
- [5 familyの軽量run directory](../artifacts/emoji_family_exploratory_v1/runs/)

## 主張の境界

正の結果に対して認める最も強い表現は、**固定済みGPT-2 MLX FP32介入cell
1件において、familyごとに中間tokenだけを置換した条件で観測された、
探索的なmatched-slot fingerprintの反復**である。

E1から、次の内容は導けない。

- 意味上の絵文字familyや、人が読める意味
- tokenizer非依存のglyph特性
- layer固有の効果
- 固定seedをまたいで頑健なrandom-control優位性
- 因果局在、component、path
- model間の一般化や独立backendでの再現
- 行動・生成への効果
- 有意性、同等性、確認、頑健性、Phase I論文gateの判定

E1はMilestone 2の分類を更新せず、C1の介入点を選ばず、C1を開かない。
E1から焦点を絞った仮説を立てる場合は、新しい公開プロトコルと、P2でもC1でも
ない未使用target bankが必要になる。
