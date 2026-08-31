# 絵文字 × 単語の不一致を前向きに追試する v0（T15-B）

[English](EMOJI_WORD_INCONGRUENCE_REPLICATION_V0.md) · [T15-A結果](EMOJI_WORD_INCONGRUENCE_INTERACTION_V0_RESULTS.ja.md)

## 固定する問い

T15-Aでは、主解析に置いた16個のmodel × depth × sign cellすべてで、response fingerprintのcoherence excessが見つかった。軸、target、model roleを丸ごと入れ替えても、この操作的な効果は再現するだろうか。

T15-Bが追試するのは、response shapeに限ったこの候補である。modelが絵文字や単語、矛盾を理解しているかどうかは検証しない。

## 入れ替えるもの

T15-Aの科学的な母集団は再利用しない。

- speed、size、openness、weight、moisture、texture、distance、fullnessからなる、記述的な新8軸;
- 新しい絵文字16個と単語16個;
- 8件ずつ6群に分け、事前に固定するsynthetic continuation target 48件;
- T15-Aに参加していないSmolLM2 1.7B baseとMistral 7B Instruct v0.3。

model rosterは母集団から無作為抽出したものではなく、境界を見るために固定した。片方は小型のbase checkpoint、もう片方はinstruction tuning済みの異なる7B architectureである。両者で同じ結果が出ても、architectureやinstruction tuningに依存しないとは言えない。

## Factorial contrastとcontrolの強化

各軸では、emoji × wordの2 × 2 gridをそのまま使う。congruent classとincongruent classには、すべての絵文字と単語が同数ずつ現れる。そのため、emoji main effectとword main effectの単純和はinteraction contrastから相殺される。

T15-Aのcross-axis controlはcyclic shift 3本だった。T15-Bではself以外の7本をすべて残す。したがって、各emoji axisは同じcheckerboard構造のまま、ほかの全word axisと一度ずつ組み合わされる。`positive`と`negative`は価値を表す語ではなく、任意に固定したpole labelにすぎない。記述的な軸を中心に据え、cross-axis partnerを全列挙することで、T15-Aの反復が価値極性や都合のよいcontrol pairingに依存していなかったかを直接確かめる。

source orderは2通り、wrapper foldは4本とも残す。2つのlate depth、2 dose、両sign、zero-hook check、emoji-main control、word-main controlも削らない。

## 固定する実行grid

- model role: 2;
- 新しいaxis: 8;
- 未使用target: 48;
- source prompt: modelあたり2,312;
- source metric row: modelあたり4,096;
- direction catalog row: modelあたり1,280;
- steering response row: modelあたり245,856、合計491,712;
- depth × dose × sign: 2 × 2 × 2;
- cross-axis shift: 7;
- generation call: 0。

新target bankのactivation RMSはT15-B内で取り直す。T15-Aの公開target baselineは流用しない。prompt本文はGitで固定したbankに置き、外部runtime receiptにはIDとhashだけを残す。

## 主たるreplication gate

元になる統計量は、T15-AのA1 estimandである。8本のtrue interaction axisに対するfull-vocabulary CountSketch response coherenceから、構造を揃えたcross-axis controlのcoherence中央値を引く。

magnitude `0.25`では、まずtarget × depth × signごとにpaired A1を計算する。次にmodelごと、targetごとに、2 depth × 2 signの中央値を取る。この48個のtarget-level valueをbootstrap unitとする。

replication supportを認める条件は、固定済み20,000回target bootstrapの2.5 percentileが、**両model roleで**ゼロを上回ること。2 modelのintersection ruleとし、片側Bonferroni alphaはmodelあたり`0.025`、family alphaは最大`0.05`とする。判断のためにmodelをpoolしない。gateの成否にかかわらず、cell-level resultとsecondary familyはすべて報告する。

## 想定する着地点

- **両modelでgate通過:** 軸とtarget bankを入れ替えても、操作的なresponse-shape候補が、固定した2 roleで前向きに再現した;
- **一方だけで再現:** 効果はmodel条件つきのまま;
- **axis/controlで消失:** 全cross-axis controlを入れると、T15-Aのexcessを区別できない;
- **targetで消失:** 新しいcontinuation bankには移らない;
- **signまたはdepthで不均一:** pool後の値の裏でcellが逆向きに割れており、強い主張はできない。

どの着地でも、意味理解、行動、causal circuit、tokenizer非依存性、scale law、model母集団への一般化は主張しない。

## T15-Cは分けて扱う

T15-Bでは、推定したinteraction subspaceそのものには介入しない。T15-Bを閉じたあとに限り、事前に定義したinteraction-residual subspaceへnecessity、sufficiency、restorationを試すT15-Cを固定できる。T15-Bが陰性だった場合、結果を見て次点componentを選び、T15-Cで救済してはならない。

## outcomeを開く前の状態

この文書、panel、target bank、実装、test、tokenizer receipt、最終manifestは、T15-B最初のmodel forwardより前にcommitする。固定した2 model roleが完全run auditを通るまで、科学的な値は開かない。
