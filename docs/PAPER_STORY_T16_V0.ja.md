# T16 論文ストーリー v0

[English](PAPER_STORY_T16_V0.md) · [統合claim table](../validation/t16_integrated_v0/claim_table.json) · [Phase I論文計画](PAPER_OUTLINE.ja.md)

状態: **投稿用ストーリーの叩き台。最終的な論文claim freezeではない。**

## 仮題

**Behaviorally Legible, Mechanistically Unresolved: Separating Emoji Fingerprints, Congruence, and Causal Mediation**

候補:

1. **From Glyph Fingerprints to Operational Semantics: Causal and Unicode Controls for Emoji Representations**
2. **Emoji Representations Are Behaviorally Legible but Not a Single Causal Circuit**
3. **When an Emoji Fingerprint Is Not a Meaning Circuit**

第一候補が最も堅い。Sufficiencyが通らなかった結果を、特定の分散回路を見つけた証拠へ
読み替えずに、観測された分離をそのまま題名にできる。

## 一文で言うと

絵文字に条件づけられた応答指紋が再現し、絵文字と語の二択判断が成功しても、
両者が同じ因果対象とは限らない。行動は読み出せるが、検証した指紋subspaceと後期bandは
より強い因果実装テストを通らず、完全同一文字列の対照からは、反復とUnicode family多様性に
よる別のtokenizer条件付き幾何が現れた。

## Abstract草案

絵文字は言語モデルの表現を調べる小さなprobeとして便利だが、視覚的な目立ちやすさ、
Unicode構成、tokenization、学習済みの関連づけが重なるため、意味や機構を過大解釈しやすい。
本研究では、証拠を4段階に分けて検証する。まず、4モデルで見つけた絵文字×語の
interaction指紋を、新しい8軸、48 target、2 model roleで事前固定し、再現した。
次に、別に凍結した二択課題で、Gemma 2 2B ITとMistral 7B Instruct v0.3が、
絵文字に割り当てた語を選び、一致・不一致の絵文字×語pairを見分けることを確認した。
4つのmodel×task gateはすべて通過した。しかし、再現済み指紋から構造的な交絡成分を除いても、
Mistralの明示的な不一致判断は因果的に支えられなかった。登録した向きでは、treatment、
sufficiency、necessityの推定値がすべて非正だった。別のLlama 3.2 3B steering endpointでは、
後期8成分bandのnecessity成分だけが通過し、sufficiencyとjoint mediation gateは不通過だった。
最後に、6つのUnicode構成familyを使った完全同一UTF対照により、同一文字列反復、
同一family内混合、family横断混合を分けた。Family横断の上乗せは8つのmodel×depth cellで
すべて正だったが、tokenizer経路への依存は残る。以上から、応答指紋、運用上の意味行動、
因果実装、Unicode条件付き幾何は、別々の経験的階層だと分かる。絵文字行動は測定できるが、
その機構は、検証した経路に局在せず、分散しているか、なお未解決である。

## この論文の本当の貢献

「絵文字回路を見つけた」という物語より、**主張の階段を実験で切り分けた**ことに価値がある。

```text
再現可能な出力指紋
          ↓ だけでは導けない
二択形式の意味行動
          ↓ だけでは導けない
その指紋による因果実装
          ↓ だけでは導けない
局所的、または十分な後期媒介
```

GlyphProbeは、ある階層で得た証拠を、次の階層の証拠へ無言で読み替えずに進むための
fail-closedな手順を示す。因果実験の負の結果は弱点ではない。階層を別々に検証する必要性を、
結果そのもので示している。

## エビデンスの背骨

| 証拠の階層 | 実験 | 結果 | 許される読み方 |
|---|---|---|---|
| 応答指紋 | T15-B | 二モデルのprospective R1 support：SmolLM2 `+0.020422` [0.012887, 0.031510]、Mistral `+0.060397` [0.056621, 0.062194] | 新しい軸、target、roleでも、狭い応答形状contrastが再現する |
| 運用上の関連づけ | T16-OSC行動 | 意味選択正答率はGemma `0.9531`、Mistral `0.9375`。両gate通過 | 固定した二択形式で絵文字と語の関連を読み出せる |
| 運用上の整合性 | T16-OSC行動 | 整合性判断正答率はGemma `0.7617`、Mistral `0.7539`。両gate通過 | 固定した一致・不一致判断を読み出せる |
| 指紋から行動への因果 | T16-OSC因果 | Treatment `-0.1484`、sufficiency `-0.0859`、necessity `-0.0547`。Gate不通過 | T15-B subspaceは、明示的な不一致判断の検証済み実装ではない |
| 後期band媒介 | T16-DP | Necessity `+0.000871`は通過、sufficiency `-0.000146`は不通過、treatmentは下限未達 | 完全な後期bandは必要成分を運ぶが、移植条件では十分でない |
| 完全同一文字列の幾何 | T16-UTF | 横断−同一family区間が8 / 8 model-depth cellで正 | Tokenizer経路を条件に、反復と構成family多様性を分けて記述できる |

## 本文の流れ

### 1. Introduction：一つの絵文字に四つの交絡が重なる

絵文字は見た目には小さいが、計算上は整っていない。人間に馴染みのある関連、Unicode構成、
tokenizer経路、モデル状態の摂動が、一つの入力に重なる。従来は最後の観測から最初の意味へ
飛びがちだった。本研究では、それぞれに別のendpointと因果テストを与える。

### 2. Measurement：まず安定した応答対象を作る

T15-Aは短くまとめ、T15-Bを測定の基点にする。重要なのは行数の多さではなく、
固定したR1解析を開く前に軸、target、model roleをすべて入れ替えた点である。
Primary-dose 8 cellのうち、正6、mixed 2だったことも本文に残す。ここで得たのは、
検証する価値のある再現対象であり、意味ではない。

### 3. Operational semantics：狭く、モデルへ直接問う

独立した8軸panelと、counterbalanceした`A` / `B`出力を導入する。Logit marginの推論と
正答率を併記する。結果は「関連づけ」と「整合性判断」と呼ぶ。「意味理解」は、
この課題だけでは制約なく確立しない、という限界を述べる箇所に限る。

### 4. Causal dissociation：再現指紋は、その判断そのものではない

ここが論文の折れ目になる。True interaction方向から、7つのcross-axis interactionと
絵文字・語の主効果をどう除いたかを示し、3つの推定値を同じ符号軸に並べる。
どれも登録方向と逆を向いたことは、単なる非有意より情報量が多い。Source fingerprintと
明示的な不一致endpointは、交換可能な因果変数ではない。

### 5. Distributed route：必要情報はあるが、十分ではない

T16-DPはT16-OSCの救済ではなく、別の機構境界として扱う。Block 24〜27の
attention＋MLP bandをbaselineへ戻すとtreatment情報が失われたが、同じ状態を移植しても
効果は再現しなかった。まずjoint IUT不通過を報告する。「このpatch操作では必要だが
十分でない」は言えるが、「回路が分散している」は留保つきの仮説として書く。

### 6. Unicode side control：表現は意味だけでは決まらない

紙幅があれば最後の主要結果、足りなければ補遺へ移す。`n=1`の厳密な同一性は、非常に
きれいな内部対照である。全深度でfamily横断上乗せが見え、GemmaとMistralでprofileが
異なる点は面白い。ただし、token数を揃えたfamily横断subsetは疎である。
将来のtokenizer-matched因果対照を導く幾何として扱い、意味分解とは呼ばない。

### 7. Discussion：三つの分離から、一つの方法論へ

議論は、次の三つへ収束させる。

1. 再現性と意味は別である。
2. 運用上の意味行動と因果実装は別である。
3. UTF同一性とtokenizer非依存な構成は別である。

方法論上の要点は、負の因果テストが説明を細かくすることにある。信頼できる観測指紋へ、
獲得していない主張が吸い込まれるのを防げる。

## 図表の計画

### 本文図

1. **Claim ladderと実験分岐。** T15-B、T16-OSC行動、T16-OSC因果、T16-DPを結び、
   赤い「does not entail」矢印を置く。
2. **行動と因果の分離。** 左に行動4セルの軸中央値区間、右に0以下となった因果3推定値。
3. **後期bandのjoint patch。** 介入模式図と、3つのIUT成分・実用下限。

### 本文表

T15-BとT16について、endpoint、主要標本単位、多重性規則、結果、許される最大主張を
一つのclaim tableにまとめる。

### 補遺図

- T16-UTFのmodel×depth×`n`別、横断−同一family heat map。
- 完全同一反復、同一family、family横断の変位profile。
- 構成family別の不均一性とtoken数完全一致subset件数。
- T15-Bの全secondary heterogeneityと、zero-guard failureの保存記録。

## 5ページ版への縮退

本文が5ページなら、次だけを残す。

1. T15-B prospective再現を一段落。
2. T16行動結果。
3. T16因果の符号反転。
4. T16-DPのnecessity / sufficiency分離。
5. 限界を一段落。

T16-UTF、T15の詳しい履歴、軸別値、engineering receiptは補遺かrepositoryへ移す。
UTF結果がなくても論文は成立するが、行動と因果の分離を外すと物語の芯が失われる。

## 投稿前に固定する主張

### 中心に置ける主張

- 試験したセルで、絵文字×語の応答形状指紋がprospectiveに再現した。
- 固定した二択形式の絵文字×語関連づけと整合性判断は、2つのinstruction-tuned model cellで成功した。
- 検証したT15-B残差subspaceは、登録した向きのまま明示的な不一致endpointを実装しない。
- 別に検証した後期bandには正のnecessity成分があるが、sufficiencyとfull mediation gateは通らない。
- Family横断混合は、8つの記述セルすべてで、tokenizer条件付きの追加変位を生んだ。

### 書いてはいけない主張

- 制約のない絵文字意味理解。
- 自然言語一般の矛盾検出。
- 固有、最小、完全、またはモデル一般の絵文字回路。
- Tokenizerから独立したUnicode構成。
- Scale lawやarchitecture law。
- Outcome-informedな因果follow-upの確認的status。
- モデル間で隠れ状態の大きさが同じ尺度にあるという前提。

## 投稿当日の編集順

1. Claim tableとabstractの表現を固定する。
2. 中心的な分離を一枚で伝えるFigure 2から作る。
3. 実験の時系列ではなく、固定した表を軸にResultsを書く。
4. Principal unit、gate、repairを再現できるだけのMethodsを入れる。
5. 負のcell、outcome-informed status、tokenization限界を、圧縮前に本文へ置く。
6. Blind claim auditとevidence link auditを最後に行い、その後に文章を磨く。

現時点のrepository evidenceだけで、完全な第一稿は書ける。ただしcamera-readyの
claim freezeではない。図と論文表をcommit済みcompact analysisから再生成し、値を照合するまで、
この区別を保つ。
