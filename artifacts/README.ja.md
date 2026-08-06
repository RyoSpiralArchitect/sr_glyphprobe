# 公開エビデンス・バンドル

[English](README.md)

GlyphProbeの研究リリースから、個人環境のパスを除いた軽量な検証資料を収録しています。

- `mlx_gpt2_parity/receipt.json`：固定GPT-2 FP32でのMLX対Transformers/MPSパリティ・速度ゲート
- `v1_standard_mlx/`：完了runのレシート、各種要約、軽量な診断表、レポート、独立artifact監査
- `MANIFEST.json`：収録ファイルのSHA-256と、Gitから除外した大容量ローカルartifactのhash
- `milestone2/`：凍結プロトコルの証拠、正確なinput-binding audit、探索・確認・二次診断runの軽量artifact、確認解析、事後感度分析
- `MILESTONE2_MANIFEST.json`：Milestone 2軽量バンドルを結び付け、完了した診断と省略したraw fileを記録するmanifest
- `milestone2/analyses/posthoc_dependence/p2/`と`milestone2/analyses/posthoc_dependence/independent_source/`：target bootstrapの各replicateでleave-one-target-group-out prototypeを作り直す、独立した事後解析
- `milestone2/analyses/diagnostics/`：末尾token一致と接頭構造均一化のpaired comparison、および同一seedによる次元fold

従来のv1 bundleでは、77,327,172 byteの条件ledger 1件とNPZ配列3件を省略しており、`MANIFEST.json`に記録している。これとは別に、`MILESTONE2_MANIFEST.json`は、14 runにわたる大容量ローカルfile 58件の省略を記録する。内訳には条件ledgerとmodel依存NPZのほか、20,000 replicateのbootstrap table 2件が含まれる。Hashは監査対象だったローカルartifactを結び付けるが、欠けたデータを復元することはできない。完全なデータが必要な場合は、該当runまたは解析を再現する。

## Milestone 2 の読み方

凍結済みv1では、layer 2が、主要ソース（+0.208363、95% CI [0.137463, 0.276893]、Holm p = 0.00143999）と独立ソース（+0.187507、[0.125489, 0.247659]、p = 0.00393996）の両方で、指定済みのトークン数・接頭構造matched controlsに対して頑健と判定された。Layer 4は両条件とも未解決だった（-0.0329465、[-0.0761085, 0.0110094]、および-0.086379、[-0.159246, -0.016917]）。詳細は [Milestone 2 結果](../docs/MILESTONE2_RESULTS.ja.md) を参照。

対照で揃えたのはトークン数とパネル単位の接頭構造であり、token IDそのものではない。Panel Cには、事前申告した意味的に近い対照`🟥`を含む。v1 analyzerはCLI順序からpanel roleを割り当てるため、凍結済み入力との正確な対応は別の`milestone2/input_binding_audit.json`で確かめた。また、v1 bootstrapは固定済みtarget効果を再標本化し、prototypeを作り直さない。事後感度分析receiptはこの依存を記述的に検査するもので、確認的statusは付けず、v1判定も上書きしない。

探索96次元のpaired median differenceは+0.047427で、正セルは25 / 36。48 / 32 / 24次元の値（+0.040200 / +0.028907 / +0.048591）は、同一seedによる代数的な畳み込みであり、sketch seed感度ではない。「何%を説明したか」という推定にも使わない。

末尾token一致と接頭構造均一化の診断はいずれも14,208行を完走し、errorは0件、zero-hook RMSは0、readinessは11 / 11だった。Random-adjustedのheadline優位量は、それぞれ+0.751225と+0.601038であり、以下のraw separation scoreとは別の評価量である。96 / 48 / 32 / 24次元における記述的なstandard-minus-suffix中央値は、+0.002624 / +0.009473 / +0.004026 / +0.009700。Standard-minus-prefixは、+0.022096 / +0.023254 / +0.011040 / +0.025387だった。96次元で正だったのは、それぞれ20 / 36セルと25 / 36セルである。これは事後的・記述的な診断で、推論や同等性の検定ではない。低次元値は同じseedによる代数的な畳み込みである。

実行時の来歴として、matched-null Aの最初のforeground processは、マシン負荷が極端に高い最中、ledger 798行で外部から中断された。Sealを保ったresumeによって、重複・欠損・error・非ゼロのzero-hook RMSなしで14,208行の正確なgridを完了した。この事象は、モデルに関する証拠でも、一般化できる速度の主張でもない。P2、独立ソース、診断runは通常どおり完了した。C1は未使用のままである。

ここにあるのは、再現可能な因果検証前のactivation screening候補と、レイヤーごとに分かれたMilestone 2対照結果である。Glyphの意味、機構、回路、因果経路、トークン化から独立した効果を確立する証拠ではない。運用上のMilestone 2は完了し、layer 2は、未使用のC1を使う対象限定型の因果プロトコルを設計できる。Layer 4は未解決のままである。
