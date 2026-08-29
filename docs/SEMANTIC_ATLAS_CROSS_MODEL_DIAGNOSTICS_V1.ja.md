# Semantic Atlas モデル横断診断 v1（T10-D）

[English](SEMANTIC_ATLAS_CROSS_MODEL_DIAGNOSTICS_V1.md) · [T10結果](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.ja.md) · [T10プロトコル](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.ja.md)

状態：**事後的な診断解析を完了。T10の一次判定は変更しない**。

T10-Dで調べるのは、T10の登録済みモデル横断・負判定の内側に、どのような不均一性があったかである。新しいmodel forwardは実行しない。CommitしたanalyzerはT10のcompact bundleを再hashし、返送済みraw archiveが与えられた場合には、FP32 activationから全retrieval predictionを直接再構成する。

## 変えない判定

T10の結論は、引き続き
`cross_model_replication_not_established_under_frozen_rule`である。統計的な部分連言検定は`p = 0.0001`で通過したが、凍結済みの二つの実用条件を満たしたcore cellは4つ中2つだった。この解析では、`0.02`の下限を下げず、core modelを入れ替えず、extension modelを昇格させず、raw最終block endpointによる登録済みfinal-state endpointの救済も行わない。

`n = 292`では、top-1差`0.02`は、全carrier-distance cellで正解が差し引き6件以上という離散的な境界になる。GemmaとOLMoは、全項目を使う8セル中7セルでこの境界を通過した。最弱セルは、それぞれ正味5件と4件だった。滑らかな正のprofileが固定した最小セル規則を通らない理由は、ここにある。ただし、これは失敗を誤りに変える説明ではない。

## 文脈profileはモデルごとに異なる

8セルのcarrier-distance差には、全モデル共通のbottleneckがない。36のmodel pairにおけるSpearman相関は中央値`-0.162`、範囲`-0.755`〜`0.610`だった。Model内profileの平方和に占める割合のモデル中央値は、次のとおりである。

- carrier：`0.198`
- distance：`0.266`
- carrier×distance interaction：`0.299`

したがって、一つの最弱セルを選び、普遍的な文脈として扱うことはできない。T11では固定した文脈gridをすべて残し、結果を見て有利なcarrierや距離を選ぶのではなく、安定性そのものを要約する。

## 全体では広いが、各モデルでは偏っている

9モデル・8文脈をまとめると、292項目中233項目で名前retrievalが少なくとも一度成功する。しかし、6モデル以上で成功するのは14項目で、9モデルすべてに共通する項目はない。Item-level advantageのmodel pair相関は中央値`0.133`、範囲`-0.063`〜`0.327`だった。

Model内の偏りも大きい。上位約10%の項目が名前hit全体に占める割合は、Mistral-Instructでは`0.374`だが、Llamaでは`0.841`、OLMoでは`0.973`、SmolLM2では`1.000`となる。最小top-1の一値だけでは、このbreadthと集中度の違いを捉えられない。

## Retrieval指標は揃うが、geometryは同じではない

返却されたfinal stateの72セルすべてで、glyph/name-minus-codepointのtop-1、MRR、paired-minus-off-diagonal marginは正だった。一方、centered linear CKAが正だったのは72セル中33セルである。9つのmodel cellを並べたとき、最小top-1差の順位相関は、MRR差の中央値と`0.971`、paired-margin差の平均と`0.802`、CKA差の平均と`0.810`だった。CKAは関連するが、retrievalと同じ情報ではない。

Codepoint textも弱い比較対象である。名前top-1の平均は`0.0738`、codepoint top-1の平均は`0.00566`で、72セル中13セルではcodepoint top-1がゼロだった。T11ではcodepoint textを一つのviewとして残すが、glyph systemとtokenizerを揃えた誤名controlも加える。Codepointだけを負対照にはしない。

## Qwen profileはscale lawではない

Qwen 4点の最小差は、checkpoint sizeの順に`0.00685`、`0.01370`、`0.01712`、`0.02397`と増える。しかし、item levelで厳密に単調増加するのは292項目中3項目だけだった。4点Spearman係数が有限となる182項目では、中央値が`0.632`、正の割合が`72.5%`である。Model sizeは各release checkpointと交絡したままであり、T11の層別化には使えても、scale lawは主張できない。

## Raw再構成とfinal norm境界

Analyzerは333のraw shardを再検証し、36本の完全なprediction arrayを再構成して、compact bundleの84,096値と比較した。不一致はゼロで、top-1差の最大絶対誤差は`1.51e-08`だった。

Finalとrawのmodel内item-geometry CKA中央値は、Gemmaで`0.836`、Qwen 3Bで`0.893`となり、残る7セルの`0.939`〜`0.980`より低い。8セルのfinal/raw top-1 profile相関はQwen 0.5Bで`-0.335`だが、Gemma、Llama、Mistral、OLMo、Qwen 7Bでは`0.847`〜`0.957`である。Final normalizationは呼び方の違いではなく、モデル依存の実質的な解析境界だった。

各model pairについて8文脈のitem-geometry CKAを中央値化し、そのmodel pair間中央値を取ると、final stateではglyphが`0.132`、Unicode名が`0.362`、codepoint textが`0.423`となる。モデル間の分岐は、記述上、glyph側で最も大きい。ただし、あるモデルがより多く、またはより少なく絵文字の意味を持つという証拠ではない。

## T11に持ち込めるもの

T10-Dから、T11では次を採用する。

- item levelの連続的なmatched-label cosine marginとMRR
- 最小セルだけではなく、retrievalのbreadthと集中度
- 2 carrier×4距離をすべて保った文脈安定性
- 全項目でのraw最終blockと返却final state
- 正規化depth trajectory用に凍結したstructure-balanced subset
- glyph systemとtext viewを分けたmodel横断item geometry

ここから意味、因果、tokenizer非依存性、scale、tuning、model一般性は主張しない。T11は新しい探索laneとして開き、T10には手を加えない。

## 再現方法

Repository rootで、返送済みT10 raw run directoryを指定する。

```bash
python scripts/analyze_semantic_atlas_cross_model_diagnostics_v1.py analyze \
  --raw-runs path/to/glyphprobe-t10-runs-8673bc51 \
  --output path/to/new-diagnostic-output

python scripts/analyze_semantic_atlas_cross_model_diagnostics_v1.py validate \
  --output path/to/new-diagnostic-output
```

Hashで固定したcompact outputは
[`artifacts/semantic_atlas_cross_model_diagnostics_v1/`](../artifacts/semantic_atlas_cross_model_diagnostics_v1/README.ja.md)に置く。
