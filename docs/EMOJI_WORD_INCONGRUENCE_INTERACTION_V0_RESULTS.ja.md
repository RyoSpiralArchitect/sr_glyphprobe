# 絵文字 × 言葉の不一致interaction v0 結果（T15-A）

[English](EMOJI_WORD_INCONGRUENCE_INTERACTION_V0_RESULTS.md) · [凍結protocol](EMOJI_WORD_INCONGRUENCE_INTERACTION_V0.ja.md) · [Closeout](../validation/emoji_word_incongruence_interaction_v0/t15a_closeout.json)

## 一段落でまとめると

凍結済みのT15-A gridで見つかったのは、modelが矛盾を理解している証拠ではなく、複数の軸に共通する**応答fingerprintの候補**だった。一次doseでは、軸内で均衡させたinteraction方向が、構造を揃えた3つのcross-axis interactionの中央値よりも一貫した全語彙応答を示した。Model × depth × signの16 cellすべてで差は正となり、20,000回のtarget bootstrap区間も全件で0を上回った。ただし、単純に応答energyが増えたわけではない。JS、total variation、logit RMS、entropy、argmax flipはいずれも不均一だった。個々のpairについても、joint-additivity残差がincongruent側で一様に大きくなる傾向はなかった。したがって、ここで記述できるのは、実験者が固定した対応関係から、軸をまたいで再利用されやすい次token分布変化の「形」が生じたことまでである。T15-Aは、公開targetとT14の結果を踏まえて選んだmodel・depth rosterを使う探索実験であり、意味理解、矛盾検出、自然な行動、因果回路、tokenizer非依存性、scale、model母集団への一般化は主張しない。

| 固定した範囲 | 完了結果 |
|---|---:|
| Model role | 4/4完了 |
| Source sequence | 5,152 |
| Steering応答 | 393,472行 |
| 公開target | 32件 |
| 軸 | 8本 |
| Depth × dose × sign | 2 × 2 × 2 |
| Generation | 0回 |
| Bootstrap | 報告する各中央値につきtargetまたはaxisをclusterとして20,000回 |

Run auditは`complete_closed_to_adaptive_selection`。解析は7 familyを全件出した探索解析であり、有意性検定も確認判定も置いていない。

## 一次の応答fingerprint family

A1では、targetごとに4つのwrapper foldと2つのsource orderを座標別中央値へ畳み込む。次に、8本のtrue interaction方向から得たCountSketch応答についてaxis間のpairwise cosineを計算し、3つの循環cross-axis対照の中央値を引く。下表は、凍結時に一次と定めたmagnitude `0.25`でのtarget中央値である。Trueとcrossはそれぞれ別にtarget中央値を示しているため、その差とpaired differenceの中央値は一致するとは限らない。95%区間は32 targetを20,000回再標本化した。

| Model | Depth | Sign | True | Cross | True − cross | 95%区間 | 正のtarget |
|---|---:|---:|---:|---:|---:|:---:|---:|
| Llama 3.2 3B base | 0.875 | − | 0.471595 | 0.290370 | +0.155243 | [0.141315, 0.198899] | 32/32 |
| Llama 3.2 3B base | 0.875 | + | 0.389174 | 0.150823 | +0.231919 | [0.224002, 0.238301] | 32/32 |
| Llama 3.2 3B base | 1.0 | − | 0.364638 | 0.130069 | +0.232216 | [0.227864, 0.235742] | 32/32 |
| Llama 3.2 3B base | 1.0 | + | 0.347363 | 0.093193 | +0.255624 | [0.249632, 0.259629] | 32/32 |
| OLMo 2 1B base | 0.875 | − | 0.195736 | 0.036709 | +0.062355 | [0.007663, 0.203024] | 22/32 |
| OLMo 2 1B base | 0.875 | + | 0.266686 | 0.096175 | +0.122757 | [0.044837, 0.341355] | 26/32 |
| OLMo 2 1B base | 1.0 | − | 0.137302 | 0.088485 | +0.050162 | [0.025334, 0.112551] | 23/32 |
| OLMo 2 1B base | 1.0 | + | 0.517765 | 0.104452 | +0.397596 | [0.363295, 0.419672] | 32/32 |
| Qwen 2.5 3B base | 0.875 | − | 0.571834 | 0.171156 | +0.411275 | [0.362851, 0.439045] | 32/32 |
| Qwen 2.5 3B base | 0.875 | + | 0.515728 | 0.120726 | +0.389015 | [0.365101, 0.407404] | 32/32 |
| Qwen 2.5 3B base | 1.0 | − | 0.364208 | 0.080717 | +0.290625 | [0.282621, 0.296236] | 32/32 |
| Qwen 2.5 3B base | 1.0 | + | 0.403310 | 0.144780 | +0.257903 | [0.248553, 0.266084] | 32/32 |
| Qwen 2.5 7B base | 0.875 | − | 0.440099 | 0.152445 | +0.263563 | [0.202882, 0.330396] | 29/32 |
| Qwen 2.5 7B base | 0.875 | + | 0.471418 | 0.377342 | +0.161788 | [0.046407, 0.214518] | 22/32 |
| Qwen 2.5 7B base | 1.0 | − | 0.263618 | 0.087359 | +0.176893 | [0.158664, 0.182732] | 32/32 |
| Qwen 2.5 7B base | 1.0 | + | 0.268406 | 0.090104 | +0.184350 | [0.170690, 0.200865] | 32/32 |

一次A1の記述区間は16本すべて正だった。Cosine計算に入ったtrue / cross-axis vectorにもzero vectorはない。応答の「形」が繰り返された点はきれいだが、多重性を補正した有意性検定ではなく、公開targetを確認bankへ昇格させる結果でもない。

## Source診断で解釈を絞る

A0は、個々のincongruent pairについて、frame相対の`pair − emoji − word` residual RMSがcongruent pairより大きいかを測る。A3は別の問いで、均衡させたtrue interaction方向のsource RMSと、cross-axis方向のRMSを比べる。区間はいずれも8軸を再標本化した。

| Model | Depth | A0 incongruent − congruent residual RMS | A3 true − cross direction RMS |
|---|---:|:---:|:---:|
| Llama 3.2 3B base | 0.875 | −0.000898 [−0.006287, 0.001590] | +0.009549 [0.003003, 0.012452] |
| Llama 3.2 3B base | 1.0 | −0.002096 [−0.010420, 0.001454] | +0.021266 [0.005608, 0.027678] |
| OLMo 2 1B base | 0.875 | −0.001376 [−0.003758, −0.000035] | +0.001366 [−0.001213, 0.003739] |
| OLMo 2 1B base | 1.0 | −0.006660 [−0.011792, −0.002203] | +0.004937 [−0.001378, 0.008668] |
| Qwen 2.5 3B base | 0.875 | +0.003849 [−0.023329, 0.037773] | +0.065395 [0.027668, 0.074031] |
| Qwen 2.5 3B base | 1.0 | −0.002306 [−0.106844, 0.024530] | +0.123474 [0.046869, 0.170550] |
| Qwen 2.5 7B base | 0.875 | +0.008598 [−0.030837, 0.027171] | +0.103704 [0.054355, 0.160173] |
| Qwen 2.5 7B base | 1.0 | −0.136574 [−0.223462, 0.070531] | +0.284244 [0.141480, 0.421626] |

A0は正区間が0、負区間が2、mixedが6だった。個々のpair residualの大きさには、incongruent側で一貫して増える傾向がない。A3は8 cell中6 cellで正、OLMoの2 cellではmixedとなった。全modelに共通して最も明瞭なのはA1の応答coherenceである。Source strengthはLlamaとQwenでは支えになるが、普遍的な説明にはならない。

## Energy・主効果・語順では簡単に説明できない

下表は、一次doseにある16本のmodel × depth × sign区間を分類したもの。Mixedには、0に接する区間と0をまたぐ区間を含む。

| Familyとendpoint | 正 | 負 | Mixed | 合計 |
|---|---:|---:|---:|---:|
| A2 true − cross応答、JS | 8 | 3 | 5 | 16 |
| A2 true − cross応答、total variation | 6 | 3 | 7 | 16 |
| A2 true − cross応答、logit RMS | 9 | 5 | 2 | 16 |
| A2 true − cross応答、entropy change | 7 | 6 | 3 | 16 |
| A2 true − cross応答、argmax flip | 0 | 0 | 16 | 16 |
| A4 word-main − emoji-main、JS | 8 | 5 | 3 | 16 |
| A4 word-main − emoji-main、total variation | 5 | 6 | 5 | 16 |
| A4 word-main − emoji-main、logit RMS | 4 | 9 | 3 | 16 |
| A5 emoji→word − word→emoji、JS | 3 | 6 | 7 | 16 |
| A5 emoji→word − word→emoji、logit RMS | 7 | 6 | 3 | 16 |

A1の反復を、「true interactionの方が常に強い」「wordがemojiを支配する」「emojiがwordを支配する」「片方の語順が勝つ」のいずれかにまとめることはできない。このdoseのargmax endpointにも情報は乏しく、A2・A4・A5のargmax-flip中央値は全区間が0に接している。

## Depthとdoseにも共通則はない

Magnitude `0.25`でA1のfinal-minus-late depth contrastを見ると、正が4、負が3、mixedが1だった。Llamaは両signで正、Qwen 2.5 3Bは両signで負。OLMoとQwen 2.5 7Bはsignによって分かれた。16本のdepth × sign cellに対する`0.25 − 0.125` dose contrastは、負が9、正が1、mixedが6だった。正区間は、OLMo depth 1.0・positive signの1本だけである（`+0.027062`、区間`[0.007392, 0.074544]`）。

Doseを上げてもcoherenceは単調に強くならず、depthを後ろへ動かした効果もmodel間で揃わない。このgridからdose lawやscale lawは導けない。

## Outcomeを開いた後の実装修復

凍結済みのv0 analyzerは、解析fileもmodel値の表示も行わないまま、A0でfail closedした。各congruence classの反復数を8と仮定していたが、凍結factorialの実数は2 cell × 2 source order × 4 wrapper = 16である。ただしassertionまでにprocessは応答値を読み込んでいたため、この修復は明示的にpost-openとして扱う。

Versionを分けたv1修復で変更したのは、構造上のassertionを8から16へ直した一点だけである。Estimand、family、endpoint、model、depth、dose、sign、target、axis、control shift、集約法、bootstrap seed・回数、claim boundaryは変えていない。元の失敗receiptとrepair manifestを残し、この手続き上の制約も結果の一部として公開する。

## 着地点と次のgate

T15-Aの着地点は、**複数modelにまたがる探索的な非加算応答fingerprint候補**である。均衡させたtrue pairingから生じる語彙応答の形は、checkerboard対照よりも軸をまたいで繰り返された。一方、応答energy、主効果の優劣、語順効果は揃っていない。これは因果実験へ渡せる候補であって、意味に関する結論ではない。

同じbankでの救済や、結果を見てからのcomponent探索は行わない。T15-Cへ進むなら、次を事前に固定する。

- 今回の候補定義に使っていない新しい運用軸;
- 新しい未使用target bank;
- 独立したmodelまたはbackend role;
- interaction-residual subspaceへの介入;
- outcomeを開く前に固定したnecessity・sufficiency・restoration検定。

この条件を満たすまでは、`confirmatory_status`、`semantic_understanding_claim_authorized`、`causal_claim_authorized`をすべて`false`に保つ。T15-AはPhase Iの論文gateを閉じない。

## Evidence anchor

| Evidence | Anchor |
|---|---|
| 凍結protocol | commit `b48b1c9` |
| Runtime helper契約検査 | commit `d10e6b4` |
| 最終実行freeze | commit `72add92`; manifest SHA-256 `d528276748997331c0864b7af1b5bbd75b74d7f771f4d94b7f5ae868d0b6030d` |
| Tokenizer preflight | [tokenizer_preflight.json](../validation/emoji_word_incongruence_interaction_v0/tokenizer_preflight.json), SHA-256 `e68a40571cc3271b74aae0034bb3eba3bfaea668373975405726a7223c9d164d` |
| 保存したv0 failure | [analysis_v0_failure.json](../validation/emoji_word_incongruence_interaction_v0/analysis_v0_failure.json) |
| 解析repair | commit `ea658b9`; manifest SHA-256 `d72cb667a0f0d1a37936a88d56a0b6640d9f7f34fe85e1b8faafd70fde3803d8` |
| 完全なrepair済みaggregate | Furnace path `/home/ryospiralarchitect/scratch/glyphprobe-t15-analysis-repair-v1-ea658b9/analysis.json`; SHA-256 `f089b31fbea245ad9fe4e5727c7dc618fa38e79bc27474c76ef435bd51fec5fe` |
| Run root | `/home/ryospiralarchitect/scratch/glyphprobe-t15-runs-72add92-r2` |
| Compact result | [t15a_closeout.json](../validation/emoji_word_incongruence_interaction_v0/t15a_closeout.json), SHA-256 `d9ad4842177448501acdf2800349f50c92cceac3ccc2a6526a7fc8bceb160f87` |

完全なaggregateとraw ledgerは、表に示した炉上のpathへ保存している。Hashで同一性は確認できるが、compact closeoutは未完了のarchive deposit gateを置き換えるものではない。
