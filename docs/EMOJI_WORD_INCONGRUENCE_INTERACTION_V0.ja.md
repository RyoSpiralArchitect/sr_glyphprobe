# 絵文字 × 言葉の不一致interaction v0（T15-A）

[English](EMOJI_WORD_INCONGRUENCE_INTERACTION_V0.md) · [T14結果](EMOJI_STEERING_T14_X_T14_C_RESULTS_V0.ja.md)

## 凍結する問い

外部から「そぐわない」と定義した絵文字と言葉の組が、単なる2方向の加算では説明できないhidden-state interactionを作り、そのsteering応答が構造を揃えたcross-axis interactionより共通性または強度を持つかを問う。

T15-Aは探索である。4 modelと後期depth 2点は、T14で符号付きmodel・depth heterogeneityを見た後に選んでいる。独立確認ではない。

## 2 × 2にする理由

各概念軸に絵文字2個と言葉2個を置き、4 cellをすべて使う。

| 温度の例 | `hot` | `cold` |
|---|---|---|
| 🔥 | congruent | incongruent |
| ❄️ | incongruent | congruent |

同じ軸では、各絵文字と各単語がcongruent / incongruentに1回ずつ現れる。Interaction方向は次で定義する。

```text
incongruent 2 cellのhidden state平均
− congruent 2 cellのhidden state平均
```

表現が単純な`emoji主効果 + word主効果`なら、バランスしたcontrastは厳密に相殺される。残差を非加算pair interaction候補として測れるが、意味理解とは呼ばない。

## 固定populationと対照

温度、感情、上下、昼夜、評価、正誤、色、音量の8軸を固定する。ラベルは実験者が指定した運用上の対応であり、modelがその意味を表現しているという主張ではない。

Core gridは、絵文字→言葉 / 言葉→絵文字の両語順と、共通suffixを持つ4 wrapper foldで反復する。Word axisを循環移動する3組のcheckerboard interactionを、同じ2 × 2構造の対照にする。これはcross-axis構造対照であり、意味的に完全に無関係だと保証するものではない。同じjoint grid内のemoji主効果とword主効果もsteeringする。

Source activationは固定wrapper suffixの最終tokenで読む。最終実行freezeより前にmodel別tokenizer preflightを行い、source order × wrapperごとに最終token IDが厳密に共通であることを要求する。Token数の完全一致は要求しないが、core contrast内のemoji identityとword identityは厳密に均衡する。

## 実行grid

- model: OLMo 2 1B base、Llama 3.2 3B base、Qwen 2.5 3B base、Qwen 2.5 7B base;
- depth: 正規化0.875と1.0;
- magnitude: 0.125と0.25。一次記述doseは0.25;
- sign: 両方;
- target: 公開済みprestage target 32件すべて;
- source sequence: modelごとに1,288件;
- steering応答: modelごとに98,368行、合計393,472行;
- generation: 0回。

Pair、emoji-only、word-only、empty frameのactivationを同じ構文で取得する。Frame相対の`pair − emoji − word`を、別のsource-level加算性診断に使う。

## 凍結解析

一次記述familyでは、true interaction方向が作る全語彙CountSketch応答fingerprintのaxis間共通性から、3つのcross-axis構造対照の中央値を引く。Target promptを標本clusterとし、4 model、両depth、両sign、両doseをすべて表示する。

二次familyでは次を全件報告する。

- joint-additivity residualのincongruent-minus-congruent;
- true-minus-controlのJS、total variation、logit RMS;
- true-minus-controlのsource direction RMS;
- word-main minus emoji-main応答;
- source order感度;
- depth・dose heterogeneity。

Targetまたはaxis単位の各中央値に、固定20,000回percentile区間を付ける。T15-Aには有意性検定も確認判定も置かない。

## きれいな着地点

- **共通の非加算interaction:** バランス方向がsourceで安定し、steering fingerprintもcross-axis対照より共通する;
- **相殺または増幅:** 不一致で応答energyは変わるが、共通fingerprintは作らない;
- **word / emoji支配:** distinct interactionなしに、一方の主効果だけが一貫して大きい;
- **加算null:** frame相対残差とtrue-minus-control steering差が0付近に残る;
- **heterogeneous regime:** sign、order、depth、modelで向きが変わり、T14の境界地図と連続する。

どの着地点も、意味、矛盾検出、自然な行動、因果回路の主張を認めない。

## 後の因果gate

T15-Aから候補が得られた場合も、T15-Cには新しいaxis、新しい未使用target bank、独立modelまたはbackend roleが必要になる。直接の介入対象はinteraction-residual subspaceである。不一致activationから除去し、congruent activationへ加え、除去後に戻す。T15-Aで次点componentを選んだり、公開targetを因果主張へ再利用したりはしない。
