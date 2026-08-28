# Mistral 7B semantic atlas batch-one v1 evidence

[English](README.md) · [結果](../../docs/MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1_RESULTS.ja.md) · [Protocol](../../docs/MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1.ja.md)

このcompact bundleは、892-itemのcanonical batch-one取得、bit-exact capture
validation、完全144-cell記述解析、失敗したbatch-64 validation、batch-shape集約感度、
576-cellのtoken構造感度を結び付ける。

Canonical runは3 view、2 carrier、4距離、9 layerに対し5,352 model forwardと
192,672本のFP32 residual vectorを持つ。Raw 28 shardはすべて検証に合格した。固定18-caseの
batch-one recaptureはbit-exactだった。292-item reserveへのmodel forwardは0である。

Raw activation約3 GiBと64,224 item-level rowは意図的にGit外に置く。このbundleには
run/session receipt、2つのcapture validation receipt、全aggregate cell row、layer summary、
正確なhashを含める。機械可読な入口は`PUBLIC_MANIFEST.json`。

Evidenceが支えるのは探索的な後期深度glyph/name alignment候補であり、意味因果、mechanism、
確認、model一般性、Phase I paper gateではない。
