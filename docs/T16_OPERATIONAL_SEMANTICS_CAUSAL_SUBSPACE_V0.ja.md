# T16 操作的意味課題と因果サブスペース

T16-OSCは、T14/T15の分布的結果だけでは答えられなかった二つの狭い問いを扱う。第一に、
固定したinstruction-tuned modelは、emojiに割り当てたwordを選び、emoji-word pairの一致・
不一致を分類できるか。第二に、固定した構造的nuisanceと直交するT15-B interaction方向の
成分は、modelのmismatch log oddsを因果的に動かすか、である。

## Claim境界

行動課題は二択強制選択である。通過しても、操作的なassociationとcongruence judgmentだけを
支持し、制約のない意味理解や一般的な自然言語の矛盾検出は支持しない。因果課題は正だった
T15-B Mistral cellを使うため、outcome-informedなmechanistic follow-upである。通過しても、
固定endpointに対するsource-defined residual subspaceの因果効果だけを支持し、唯一または
完全な回路を同定しない。

## 行動lane

Panelは、T15-A/T15-Bのaxis labelを再利用しない新しい8軸から成る。Gemma 2 2B ITと
Mistral 7B Instruct v0.3を各model固有のchat templateで評価する。最終実行freeze前に、
両tokenizerで`A`と`B`がそれぞれ正確に1 next tokenであることを要求する。

Meaning taskはmodelごとに128 rowで、8軸、emoji 2極、prompt template 4種、answer mapping
2種を含む。Congruence taskはword 2極を加え、modelごとに256 rowとなる。Endpointは正答
logitから誤答logitを引いた値で、principal unitはprompt rowではなくsemantic axisである。

4つのmodel-task cellごとにaxis内prompt中央値を求める。固定gateは、20,000 replicateの
axis bootstrap中央値下限が0を超え、mean axis effectを統計量とする8軸の正確な片側
sign-flip p値が0.0125以下であることを要求する。4 cellすべてが通過しなければならない。

## 因果residual-subspace lane

Source arrayは、hash固定したMistral T15-Bの正規化depth 0.875と1.0のdirectionである。
各true interaction directionについて、nuisance spanは、同じsource order・held-out wrapper
foldにある同じemoji axisの7つのcross-axis interactionと、emoji/word main effectから成る。
Thin SVDでtrue directionをnuisance成分とresidual成分へ射影分解する。

各T15-B axis内で、両source orderと4 held-out wrapperを平均する。Full、residual、nuisance
projectionは同じfull-direction RMSでscaleするため、model forward前にresidualとprojection
の和がfullを復元する。7つのcross-axis controlはそれぞれ独立にunit-RMS scaleする。

固定targetはT15-B panel上のcounterbalance済みmismatch judgment 128件である。登録済み2深度
それぞれで、zero、full/residual/projectionの正負、および7 cross-axis controlの正負を測る。
Primary endpointはmismatch logitからmatch logitを引いた値である。Primary estimandは次の3つ。

1. fullの方向的antisymmetryからcross-axis control中央値を引く。
2. residualの方向的antisymmetryからcross-axis control中央値を引く。
3. fullの方向的antisymmetryからprojection-onlyのantisymmetryを引く。

3 estimandすべてで、深度pool済みaxis levelのbootstrap中央値下限が0を超え、mean axis
effectを統計量とする正確なsign-flip p値が0.05/3以下でなければならない。Zero hookと
vector restorationはengineering gateである。
結果を見て有利なdepth、axis、template、controlを選択してはならない。

## 実行境界

Tokenizer/artifact preflightのmodel forwardは0である。最終manifestはmodel loadより前にcommit
する。Runnerは固定済みlocal snapshotだけを使い、text生成を行わず、各phase前にfurnace上の
foreign GPU workloadを確認し、競合時にはcode 75で終了する。Raw ledgerはfurnace scratchに
残す。Compact analysisとreceiptは、behavior 2 roleまたは完全causal runのaudit後にcommitできる。
