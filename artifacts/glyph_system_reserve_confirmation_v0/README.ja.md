# Glyph-System Reserve Confirmation v0 コンパクト証拠

[English](README.md) · [結果全文](../../docs/GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.ja.md) · [凍結済みプロトコル](../../docs/GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0.ja.md)

このbundleは、T12で完了した一度限りのreserve confirmationを、Gitで扱える大きさに
まとめた証拠である。`H_ZWJ_FUSION`と`H_REGIONAL_DUAL`は、どちらも確認されなかった。

収録内容:

- 凍結済みconfig、manifest、design preflight
- 9 model分のtokenizer/artifact preflight receipt
- 9本のrun receiptとshard index
- 432件のitem-contrast cell行とjoint primary result全体
- 保存済み中央値、49,999回randomization 3件、各gate、intersection-union結合、
  Holm familyの独立再計算

収録しないもの:

- raw FP32 activationとshardごとのobservation
- model weight
- interventionまたはgenerationの出力。T12ではどちらのcallも0回だった。

収録しないacquisition payloadは、run receiptとshard-ledger hashで拘束している。
Raw activationを含まないため、このbundleは保存済みの推論経路を独立検証するが、
activation contrastの独立再構築やmodelの独立再現ではない。

Repository rootから次を実行する。

```bash
python scripts/validate_glyph_system_reserve_confirmation_v0_result.py \
  validate-public-bundle \
  --bundle artifacts/glyph_system_reserve_confirmation_v0
```

Primary resultのSHA-256は
`1dee4bd187c5816d809cec27c4972edb217442e7824ef172a7d5933557d491a6`である。
意味、因果、behavioral steering、tokenizer非依存性、scale、model一般性の主張は
認めない。
