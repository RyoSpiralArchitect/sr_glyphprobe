# Multifamily common-suffix carryover v0 結果

[English](MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.md) · [固定protocol](MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0.ja.md) · [T3生絵文字結果](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.ja.md) · [公開evidence](../artifacts/multifamily_common_suffix_carryover_v0/README.ja.md) · [研究ロードマップ](ROADMAP.ja.md)

## 状態

Roleを固定した2つのMLX runと、事前に定めた合同解析を完了しました。結果の型は、

```text
olmo_only_common_suffix_carryover
```

です。2文脈×全深度のmatched-slot nullは、Gemmaでは棄却されず、OLMoではHolm補正後も
棄却されました。したがってOLMoの再現は、生の絵文字に含まれる共有slot tokenから、
その1つ後ろに置いた共通tokenへ読み出しを移しても残りました。T3を「現在位置のtoken
だけ」で説明する記述は退けられます。一方、直前のtoken構造が局所的に伝わったという
説明は、そのまま残ります。

## 主結果

主統計は、family平均を引いた後のslot平方和比率を、固定した2接尾文脈×5深度で同じ
重みで平均した値です。19,999回のPCG64 drawでは、family内slotの同じ並べ替えを10セル
すべてに使います。2つのmodel-level p値を一つのHolm familyとしました。

| Model | 観測値 | Null平均 | 差 | Raw p | Holm p | 棄却 |
|---|---:|---:|---:|---:|---:|---|
| Gemma 2 2B 4-bit | 0.203443011 | 0.200044692 | +0.003398319 | 0.302950 | 0.302950 | no |
| OLMo 3 7B BF16 | 0.537464703 | 0.199977865 | +0.337486838 | 0.000050 | 0.000100 | yes |

OLMoのraw p値は、19,999 drawと観測配置から得られる最小値です。それ以上の精度は
意味しません。封印済みreceiptでも`confirmatory_status`と`phase_i_gate_closed`は
ともにfalseであり、結果は探索的・観測的なままです。

## 2つの接尾文脈

文脈ごとの値は副次結果で、個別の多重性判定は行いません。各記述値には同じ設計の
randomizationを使いました。

| Model | 文脈 | 5深度の統計 | Null平均 | 差 | 副次p |
|---|---|---:|---:|---:|---:|
| Gemma | period | 0.199064943 | 0.200039599 | -0.000974656 | 0.542250 |
| Gemma | newline | 0.207821079 | 0.200049785 | +0.007771293 | 0.191650 |
| OLMo | period | 0.538985382 | 0.199989386 | +0.338995995 | 0.000050 |
| OLMo | newline | 0.535944025 | 0.199966344 | +0.335977681 | 0.000050 |

OLMoのperiodとnewlineがほぼ同じ値になったため、一種類の接尾tokenだけを唯一の説明と
するのは難しくなりました。ただし、この2文脈は独立した追試ではありません。同じ
glyph panel、model artifact、深度、同期nullを共有しています。

## 固定した全20セル

以下はすべて副次結果です。文脈や深度を主omnibusの代わりには使えません。

| Model | 文脈 | Fraction | Layer | Slot比率 | Null平均 | 差 | 副次p |
|---|---|---:|---:|---:|---:|---:|---:|
| Gemma | period | 0.00 | 0 | 0.174106 | 0.200096 | -0.025989 | 0.994100 |
| Gemma | period | 0.25 | 6 | 0.207494 | 0.199951 | +0.007543 | 0.180350 |
| Gemma | period | 0.50 | 13 | 0.217654 | 0.200035 | +0.017619 | 0.085050 |
| Gemma | period | 0.75 | 19 | 0.202483 | 0.200045 | +0.002438 | 0.382850 |
| Gemma | period | 1.00 | 25 | 0.193587 | 0.200071 | -0.006484 | 0.660600 |
| Gemma | newline | 0.00 | 0 | 0.185929 | 0.200002 | -0.014072 | 0.855750 |
| Gemma | newline | 0.25 | 6 | 0.209157 | 0.200088 | +0.009069 | 0.172800 |
| Gemma | newline | 0.50 | 13 | 0.221039 | 0.200075 | +0.020964 | 0.109900 |
| Gemma | newline | 0.75 | 19 | 0.210167 | 0.200140 | +0.010027 | 0.204850 |
| Gemma | newline | 1.00 | 25 | 0.212813 | 0.199944 | +0.012868 | 0.217500 |
| OLMo | period | 0.00 | 0 | 0.990924 | 0.199897 | +0.791026 | 0.000050 |
| OLMo | period | 0.25 | 8 | 0.686897 | 0.199972 | +0.486926 | 0.000050 |
| OLMo | period | 0.50 | 16 | 0.441446 | 0.200022 | +0.241424 | 0.000050 |
| OLMo | period | 0.75 | 24 | 0.294227 | 0.200050 | +0.094177 | 0.000050 |
| OLMo | period | 1.00 | 31 | 0.281434 | 0.200007 | +0.081427 | 0.000050 |
| OLMo | newline | 0.00 | 0 | 0.984778 | 0.199868 | +0.784910 | 0.000050 |
| OLMo | newline | 0.25 | 8 | 0.678584 | 0.199961 | +0.478623 | 0.000050 |
| OLMo | newline | 0.50 | 16 | 0.423447 | 0.199977 | +0.223469 | 0.000050 |
| OLMo | newline | 0.75 | 24 | 0.316141 | 0.200029 | +0.116112 | 0.000050 |
| OLMo | newline | 1.00 | 31 | 0.276770 | 0.199997 | +0.076773 | 0.000050 |

OLMoは、両文脈とも最初のblock出力でほぼ完全なslot配置を示し、stackを進むにつれて
低下しました。ただし固定nullより上には残ります。これは深度profileの記述であり、
特定のmechanismが意味変数を運んでいる証拠ではありません。

## T3から何が変わったか

T3では、生の絵文字の末尾tokenを読みました。OLMoのtokenizationは厳密に
`[9468, family_token, slot_token]`だったため、同じmatched slotなら、familyをまたいで
現在tokenそのものが同じでした。T4ではperiodまたはnewlineを加え、その共通接尾tokenを
読みます。各文脈内では50項目すべての現在tokenが同一になり、生の絵文字token列全体は
直前のprefixに残ります。

| Model | T3 生絵文字 | T4 共通接尾 | T4 − T3 |
|---|---:|---:|---:|
| Gemma | 0.204304805 | 0.203443011 | -0.000861794 |
| OLMo | 0.500391869 | 0.537464703 | +0.037072834 |

この差は記述値に限ります。T3とT4を一つの推論へ統合しておらず、T4はT3からの増加を
検定する設計でもありません。

したがって更新できる主張は狭いものです。**OLMoのmatched-slot geometryは、slot token
そのものを読む位置だけに閉じず、固定した2文脈の共通token上でも1 token先まで観測
できました。** 短距離のtoken列伝播だけで説明する仮説は十分に残ります。Gemmaは、
生絵文字と共通接尾の両測定でmatched null付近でした。

## Integrityとtransfer

- 公開protocolのfreeze commitは
  `868f3be36e10bc6acd7e44caaf916b4e1ede84b9`です。
- Gemmaは`50 × 2 × 5 × 2304`、OLMoは`50 × 2 × 5 × 4096`のarrayを生成しました。
- 各runは100 model forward、intervention・generation・保護targetアクセスは0回です。
- 2つのrun validatorと合同analysis validatorはすべてPASSしました。
- OLMoの4ファイルは、mac1、furnace relay archive内、mac2で個別hashが一致しました。
  furnace GPUは使っていません。
- Compactな全array、observation、receipt、analysis、checksum、transfer receiptを公開します。

## 主張境界と次の判断

絵文字の意味、tokenizer非依存性、因果mechanism、model scaleやprecisionの効果、node差、
backend parity、behavioral steering、確認的結論、Phase I論文gateは示せません。Gemmaと
OLMoはtokenizer、architecture、size、precision、nodeが同時に異なります。

介入へ進む前の安価な次の反証として、同じ共通tokenを何token先で読むかを固定する
distance-decay carrier assayが考えられます。急速に消えるか長く残るかで、厳密に1 token
だけの局所説明と、より長いcontext traceを分けられます。ただし、それも観測実験です。
Milestone 2で必要なtokenization-matched確認controlの代わりにはしません。
