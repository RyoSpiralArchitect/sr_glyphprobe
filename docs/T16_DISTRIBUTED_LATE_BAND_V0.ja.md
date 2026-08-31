# T16 分散late-band媒介

T14-Cでは、前向きに選択した単一downstream componentがtreatment、necessity、sufficiencyを
同時に通過しなかった。T16-DPは一つの限定した代替を試す。効果は一つのmoduleへ局在せず、
後段のattention-plus-MLP band全体へ分散している可能性がある。

## 固定intervention

Model、source direction、injection site、magnitude、endpoint、nullはT14-Cから変更しない。
Llama 3.2 3Bのblock 23出力へT14 treatmentを加える。Mediatorはblock 24から27までの各
`attn_out`と`mlp_out`を順序付きで全て含む8 componentのjoint setである。Band全体を結果前に
固定し、componentのrank付けや除外は行わない。

各condition batchで、一回のtreatment passが8 component全てをcaptureする。Necessityは
treatment runの8 component全てをbaseline captureへ置換する。Sufficiencyはsource vectorを
injectせず、baseline runの8 componentをtreatment captureへ置換する。Restorationはtreatmentを
再実行し、capture済みtreatment componentを復元する。置換は自然なblock順序を保つ。

## 新規targetとdecision

最終freeze commitをpushした後だけ、決定論的な192 row・12 stratum target bankをGit外に
materializeする。Prompt bodyは研究transcriptへ出力しない。決定論的に再構成したT14 C1 v2
bankまたはpublic localization bankとの完全一致が一つでもあれば停止する。

三つのtarget-level estimandは、structured-minus-nullのtreatment JS、necessity-drop JS、
sufficiency JSである。三成分intersection-union testでは、20,000 replicateのstratified
bootstrap下限が各固定practical floorを超え、99,999 drawの片側sign-flip p値が全て0.05未満で
なければならない。Restoration、同一batch内zero、固定済みT14 upstream-sham evidenceもgateとなる。

## Claim境界

通過しても、一つの固定modelと操作的endpointにおけるlate band全体のjoint mediationだけを
支持する。8 componentが個別に必要、bandが最小、唯一または完全なemoji circuitであるとは示さない。
失敗した場合、この固定distributed-band試行は閉じ、同じbankからsubset、site、sign、target
stratum、別endpointを選んで救済してはならない。

