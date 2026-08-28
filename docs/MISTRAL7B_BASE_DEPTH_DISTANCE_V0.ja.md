# Mistral 7B base depth-by-distance v0

[English](MISTRAL7B_BASE_DEPTH_DISTANCE_V0.md) · [T6結果](MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.ja.md) · [ロードマップ](ROADMAP.ja.md)

状態: **prospective freeze・T7 model forward 0**。このprotocol、実行code、test、
zero-forward preflight、artifact receipt、checksum manifestを1つの公開commitで結び付けた
時点でfreezeが完了する。

## このcellを選ぶ理由

T6は全深度を平均したdistance-attenuation endpointを通過しなかった。ただし完全な副次
profileでは、Mistral 7B Instruct cellの最初の固定深度だけで強い減衰があり、その後は
かなり平坦になるという記述的な形が見えた。slot-scramble変換はT6の同期permutation
nullを単に並べ替えるだけなので、同じ400 forwardを反復しても新しい情報にならない。

そこでT7では、まだactivationを見ていない
`mistralai/Mistral-7B-v0.3@caa1feb…`の1 cellを固定する。T6 Instruct modelと同じv0.3
世代のbase checkpointで、architecture規模は同じであり、tokenizer rosterも一致する
見込みである。baseの結果は未観測である。

ただしmodelとendpointはT6を見た後に選んだ。したがってprospectiveなのは、このbase
cell自身の未観測結果に対してだけである。独立確認ではなく、base/instructが1組だけ
なのでinstruction tuning効果も同定できない。

## 固定design

公開済み5 family × 10 slot emoji panel、8 tokenの2 carrier（`" a"`と`" |"`）、距離
`[1, 2, 4, 8]`、`resid_post`深度 `[0, .25, .5, .75, 1]`はT6から変えない。
Mistralで解決されるlayerは `[0, 8, 16, 24, 31]`。glyph-plus-carrierの完全な文字列を
各readout位置でforwardし、合計は厳密に400 forward、2,000 capture vectorとする。

介入、生成、behavior scoring、protected target accessは行わない。

## 主endpoint

Carrier・distance・depthごとにfamily平均を引き、固定したmatched-slot fraction

`SS_slot / (SS_slot + SS_interaction)`

を計算する。主判定は1つのintersection-union testである。

1. 距離1 recurrenceは、両carrier・全5深度の等重み平均
2. 各深度のattenuationは、距離へ重み `[0.375, 0.125, -0.125, -0.375]`を与え、
   両carrierを等重み平均したcontrast
3. interaction統計量は、深度0のattenuationから後続4深度の等重み平均を引いた値
4. IUT p値はrecurrenceとinteractionのp値の大きい方

Nullでは、基準family以外の4 family内でmatched-slot labelを独立に置換し、同じ置換を
全carrier・distance・depthへ同期する。PCG64 seed `2026082801`で19,999 drawを行う。
1つのIUTをalpha 0.05で判定するため多重性補正はない。通過には両成分が必要である。
深度別、carrier別、tail、元のT6 endpoint、base/instruct比較は副次であり、失敗した
IUTと差し替えない。

## Artifactとmodel forward 0 gate

公式の公開revisionは`caa1feb0e54d415e2df31207e5f4e273e33509b1`へ固定する。
ローカルartifactでは、重複する14.5 GBの`consolidated.safetensors`を除外し、
Transformers用3 shard・index・tokenizer/configだけを含める。Freeze commitの前に、
model forward 0のpreflightで、正確なfile manifest、architecture次元、parameter数、
token列を記録する。

このpreflightは合格した。選択した12-file artifactは`14,499,379,264` byteで、path非依存の
manifest SHA-256は
`1ee90f904de614fd2e1088e9e978fa5b9d36d1a855807764fb8f91cacfd8d05e`である。Index内の
全tensorはBF16で、合計`7,248,023,552` elementだった。Base tokenizerは、両carrierの
50/50 round tripを含め、固定したT6 Mistral roster hashと完全に一致した。Model weightは
loadせず、model forward、介入、生成、protected-target readはすべて0だった。

Model load直前には`spiral status`を再確認し、競合GPU processがないことを確かめる。
Runnerは最初のforwardより前に、公開freeze、local artifact hash、runtime version、CUDA
device、BF16 parameter dtype、model class、block path、token roster、carrier identity、
round tripを検証する。

## 登録する解釈

分岐は、両成分通過、recurrenceだけ、interactionだけ、どちらも不通過、の4つで尽くす。
どの分岐でも固定した1 modelと40件のcarrier × distance × depth rowをすべて残す。

IUTが通過しても示せるのは、選択済み未観測base cellに固定した深度依存の観測profile
までである。意味、機構、因果、behavior、単調減衰、永続memory、tokenizer因果、
instruction tuning効果、model一般性、独立確認、Phase I paper gate完了は示さない。
