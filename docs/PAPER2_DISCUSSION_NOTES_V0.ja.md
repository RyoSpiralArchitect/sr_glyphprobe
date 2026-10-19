# 論文第2弾の考察Note：条件付き経路効果からK/Vの分解へ

[English](PAPER2_DISCUSSION_NOTES_V0.md) | [T22の結果](T22_CPU_LEXICAL_RESULTS_V0.ja.md) | [第1論文の最終監査](POST_REVIEW_EVIDENCE_RESULTS_V0.ja.md)

状態：**結果観測後の解釈と研究課題、2026-10-20 JST**。
このNoteはT22 CPUの8項目の結果を見た後に書いたもの。
事前登録、新しい確認実験、第1論文の判定改訂ではない。
今後の追記も、日付・証拠・解釈・代替説明・次に区別する測定を分けて記録する。

## 1. 第1論文から残った論点

第1論文は語彙検索から、条件を限定した介入へ進んだ。
T19の9構成の比較は、対応する対照の下で語彙的構造を支持するが、
意味の媒介因子を確立してはいない。T19/T20で試したrank-8の媒介説明は、
それぞれの指定された検定で支持されないか、較正不能だった。
これは他のすべての部分空間や機構の否定を意味しない。

T21-Cが介入の正の結果を与える。block 21のreadout残差を同じ項目の
codepoint-view状態に置き換えた上で、後段のglyph位置にdonorのK+Vを
入れると、語彙cosine marginが動いた。適格な残り195項目をすべて保持し、
位置調整済みdecrement/restorationの平均は **0.002326 / 0.002267**。
元の5対比のfamilyでは同時下限が正だった。一方、絶対glyph効果の平均top-1
decrement/restorationは両方 **ゼロ**。その後の自項目・競合への分解は記述的で、
新しい確認的検定を加えていない。

| 残る問い | 既存の証拠だけでは決まらないこと |
|---|---|
| Key、value、その同時効果 | T21はKとVを同時に変更するため、margin変化を介入要因ごとに割り当てられない。 |
| 自項目との整列か、競合か | margin変化には自項目alias、最大競合、両方が寄与しうる。最大競合のidentityも変わりうる。 |
| 誘導した計算か、通常の計算か | codepoint残差resetは推定対象の一部。自然な無介入文脈での必要性・十分性は試していない。 |
| 位置か、対応する曝露量か | token数の一致は、attention mass・意味内容・すべての位置特性を一致させない。 |
| 記号種への特異性 | 同じ経路介入を非emoji記号panelと比較していない。 |
| readoutか、行動か | 固定galleryのcosine、検索順位、生成行動は異なる結果変数。生成行動は測っていない。 |
| 一般性と新しい確認実験 | 1 checkpoint・固定donor/gallery・2 carrierから普遍的機構は定まらない。元のmatched poolに未使用項目は残っていない。 |

過去のp2とc1のv1 bankは保護を継続し、新しい設計や確認に使用しない。
新たな確認母集団は別途準備して予約する必要がある。8項目canaryも評価済みの
384項目panelも、解析を変えただけで未露出にはならない。

## 2. 第2論文のフレーミング

作業上の問い：**readout状態への介入を固定したとき、局所的なkey/value介入は
語彙readoutと後段のattentionをどう変えるか。**

最初の貢献は、制御した介入の分解と、その測定可能な帰結にある。
Kに「経路」、Vに「意味」を最初から割り当てない。同じlayer入力において、
V-only置換はそのlayerで使うattention weightsを保つ。しかしattention出力が
変わると、次layerの残差・query、さらに後段のattentionが変わりうる。
K-only置換はvalueの混ぜ方を変え、そのvalueに含まれる情報も依然として関わる。
どちらも独立した心理的変数ではない。

単一attention headでもweightsとvaluesには同時依存性がある。
query固定でweightsをa0からa1、valuesをv0からv1へ変えると、
交差項 `(a1 - a0) @ (v1 - v0)` が生じる。複数layerへの介入、残差更新、
正規化、cosine scoring、競合の最大値選択によってさらに依存性が加わる。
したがって `Delta_KV - Delta_K - Delta_V` は有用な記述的非加算性対比だが、
生物学的・意味的な相互作用の同定でも、valueが運ぶ意味の割合でもない。

論文では、局所介入の正しさ、保存したattention/readout状態の変化、
今後検証する課題成績、という3段階を結び付けつつ区別する。
ある段階の結果だけで次の段階まで確立したことにはしない。

## 3. なぜこれを最初の実験にしたか

[最初の判断メモ](T22_KV_DISSECTION_FIRST_STEP_V0.ja.md)では、
reference / K-only / V-only / joint-KVの比較を選んだ。
T21のblock-21 reset、blocks 22–27、distance 8、pipeとarticle-aのcarrier、
事前に決まったtoken数一致の2 donor、glyph対同数suffixの比較を保ちながら、
T21の曖昧さを一つ分解するためである。置換はquery局所的で、
readout queryだけにdonor tensorを代入する。

元の露出済みcanary 8項目を使い、解釈に先立って実装のparityを確認した。
過去のGPU配列が利用できなかったため、固定したLlama 3.2 3B BF16 checkpointで
CPU上の再取得を行った。同じCPUでstock、過去adapter、neutral、no-op、roundtrip、
off-targetの検証を通過したが、過去のRTX 5090実行の完全再現を確立したわけではない。

その後、[語彙protocol](T22_CPU_LEXICAL_CANARY_V0.ja.md)で語彙結果を見る前に
scoringの選択を固定した。自項目aliasと元の128 source aliasを保ち、
同じCPU runtimeで状態を再取得した。activeとneutralは同一batch slotを使う。
各項目について：

`E = active - neutral`

`Delta_X = mean_carrier,donor(E_suffix,X - E_glyph,X)`

margin Deltaが正なら、suffix置換よりglyph置換の方が自項目対最大競合marginを
大きく減らす。絶対glyph decrementは別に `-mean(E_glyph,X)` とする。
標本は **target 8項目** であり、carrier/donorを32個の独立観測とは数えない。
p値、母集団信頼区間、有効性の閾値、勝者となるoperationは指定していない。

## 4. 最初の読みと、残る代替説明

| Operation | 位置調整済みmargin decrement平均 | 項目の標本SD | 項目範囲 |
|---|---:|---:|---:|
| Reference | 0 | 0 | 0〜0 |
| K | +0.000437 | 0.001765 | −0.002796〜+0.002813 |
| V | +0.001805 | 0.003647 | −0.003502〜+0.009042 |
| KV | +0.000899 | 0.004175 | −0.007956〜+0.005689 |

**観測。** この条件付き計算ではV-only置換によって語彙readoutが動く。
reference以外の各operationは6項目が正、2項目が負。
非加算性対比の平均は **−0.001343**
（標本SD 0.001894、範囲 −0.003930〜+0.001195）。

**読み。** この8項目では、別々のKとVの対比を足してもjoint-KVの結果を数値的に
再構成できない。Vの標本平均が最大だが、母集団での順序の証拠でも、
次の実験をVだけに絞る根拠でもない。項目間の異質性や固定donor/galleryの選択は、
一般的な説明に対して依然として重要な代替説明となる。
非加算性はattention内、後段layer間、非線形なscoringのどこからでも生じうる。
この比較だけでは発生場所を特定できない。

**観測。** Vの位置調整済みown-cosineとmax-competitor成分は
+0.001094と−0.000711で、差がmargin対比+0.001805となる。
Kの対応する成分は−0.009472 / −0.009909、KVは−0.008112 / −0.009010。
これは位置調整済みの対比であり、生のcosine変化ではない。
位置調整済みtop-1 decrementはK/KVが−0.0625、Vがゼロで、
非ゼロのtop-1対比はすべて項目4に由来する。
平均margin decrementが正でも、それに対応するtop-1低下は意味しない。

**読み。** 「自項目の語が取り除かれた」という一次元的な説明では足りない。
最大競合の変化も含め、自項目との整列と競合の両方を残す必要がある。
離散的な固定galleryの結果から、生成行動の改善も示せない。

**観測。** V-onlyの局所attention weightsは、各layer自身の入力において完全一致する。
それでもactive対neutralのheadごとのattention L1距離の平均は、block 22で0、
block 23で0.008635、block 27で0.028619となる。

**読み。** 後段queryに関する留保は、理論上の注意だけでなく実測された。
V-onlyが保つのは局所的な重み付けであり、その後のattention軌跡全体ではない。
reference attentionへのclampは別の反実仮想を調べる候補だが、未実施であり、
そのclamp自体も研究対象の計算を変える。

## 5. 次の測定と、説明を変える結果

次の実証段階は引き続き、**評価済み384項目での探索的比較**。
4 operationすべてと、凍結した候補・donor・gallery・位置対照を保つ。
これは **未実施**。8項目の符号によって採用・中止・調整しない。
取得前にCPUでの正確な仕様、集約、診断、実行予算を公開し、
実装上必要な変更は結果を見る前に記録する。
この事後的Noteから母集団の数値的な判定閾値を与えることはしない。

広いpanelでは、今回の符号、ばらつき、競合パターン、非加算性が、
その露出済みpanel内でより広く見られるかを調べられる。
ゼロ近傍や逆方向のパターンも残し、それらが現れれば8項目からの読みを弱める。
正の結果が安定しても、条件付きの探索的証拠にとどまり、
意味の輸送や新しい確認実験にはならない。

それ以降の候補には、それぞれ別のprospective設計が必要となる：

| 現在未実施の候補 | 区別に役立つ可能性があること |
|---|---|
| 後段attentionを明示したreferenceへclampし、介入blockを分ける | clamp条件の下で、直接の局所value混合と、後段計算へ伝播する変化を比べる。 |
| own/competitor/donor scoreを残し、対照間のattention massを調べる | 相対的整列と競合、token数一致の下に残る実効曝露量の違い。 |
| intactとreset条件を比較する | 人工的な残差reset文脈への依存性。 |
| 対応する非emoji記号、別carrier/donor、新たに予約するbank | 記号種への特異性と、この露出済みpanelを超える一般性。 |
| 順位と生成課題の結果変数を事前指定する | 幾何学的変化に測定可能な運用上の帰結があるか。 |

これらは設計する問いであり、今回答えが出たという主張ではない。
特に、後段attentionの差を観測しただけでは、それが語彙効果をどれだけ媒介するかは
同定できない。

## 6. 証拠の経路と再現性

実装の詳細、全8項目の値、取得回数、hash、model/runtimeの固定値は、
[実装記録](T22_CPU_ENGINEERING_V0.ja.md)、
[凍結した語彙protocol](T22_CPU_LEXICAL_CANARY_V0.ja.md)、
[全結果](T22_CPU_LEXICAL_RESULTS_V0.ja.md)を参照する。
最初の提案と語彙protocolは、歴史的文書として取得前の状態表記を保つ。
現在の状態は結果文書とこのNoteが示す。

PRには実装検証の親NPZ 8ファイルとalias/score archiveを、receiptのbyteを変えず
保存する。独立したNumPyのみの監査は、512行の66,048 cosine、全paired対比・要約、
CSVとの対応、attention診断を再計算する。モデルforwardや取得時に省略した
完全tensorを再実行するものではない。他のcheckoutでも使える再計算commandは
結果文書に記す。数値再構成は1回の取得に対する監査であり、独立した科学的再現ではない。
