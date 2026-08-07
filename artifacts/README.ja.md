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
- `emoji_family_exploratory_v1/`：E1のtokenizer preflight、全記述解析、5 family runごとの軽量file 15件
- `EMOJI_FAMILY_EXPLORATORY_V1_MANIFEST.json`：E1の公開payload 82件をSHA-256で結び付け、省略したraw ledgerとarrayを記録するroot manifest
- `llama32_3b_mps_emoji_transport_v2/`：別versionとして用意したE2 MPSの証拠root。Static freeze時点では英日案内だけを置き、analysis treeがなければ有効な科学的結果は未公開である。
- `../validation/llama32_3b_mps_emoji_transport_v1/preflight_failure_receipt.json`：廃止済みv1のtokenizer preflight failure記録。Model weightの読み込みとmodel forwardの前に停止しており、科学的outcomeの証拠ではない。

従来のv1 bundleでは、77,327,172 byteの条件ledger 1件とNPZ配列3件を省略しており、`MANIFEST.json`に記録している。これとは別に、`MILESTONE2_MANIFEST.json`は、14 runにわたる大容量ローカルfile 58件の省略を記録する。内訳には条件ledgerとmodel依存NPZのほか、20,000 replicateのbootstrap table 2件が含まれる。Hashは監査対象だったローカルartifactを結び付けるが、欠けたデータを復元することはできない。完全なデータが必要な場合は、該当runまたは解析を再現する。

## Milestone 2 の読み方

凍結済みv1では、layer 2が、主要ソース（+0.208363、95% CI [0.137463, 0.276893]、Holm p = 0.00143999）と独立ソース（+0.187507、[0.125489, 0.247659]、p = 0.00393996）の両方で、指定済みのトークン数・接頭構造matched controlsに対して頑健と判定された。Layer 4は両条件とも未解決だった（-0.0329465、[-0.0761085, 0.0110094]、および-0.086379、[-0.159246, -0.016917]）。詳細は [Milestone 2 結果](../docs/MILESTONE2_RESULTS.ja.md) を参照。

対照で揃えたのはトークン数とパネル単位の接頭構造であり、token IDそのものではない。Panel Cには、事前申告した意味的に近い対照`🟥`を含む。v1 analyzerはCLI順序からpanel roleを割り当てるため、凍結済み入力との正確な対応は別の`milestone2/input_binding_audit.json`で確かめた。また、v1 bootstrapは固定済みtarget効果を再標本化し、prototypeを作り直さない。事後感度分析receiptはこの依存を記述的に検査するもので、確認的statusは付けず、v1判定も上書きしない。

探索96次元のpaired median differenceは+0.047427で、正セルは25 / 36。48 / 32 / 24次元の値（+0.040200 / +0.028907 / +0.048591）は、同一seedによる代数的な畳み込みであり、sketch seed感度ではない。「何%を説明したか」という推定にも使わない。

末尾token一致と接頭構造均一化の診断はいずれも14,208行を完走し、errorは0件、zero-hook RMSは0、readinessは11 / 11だった。Random-adjustedのheadline優位量は、それぞれ+0.751225と+0.601038であり、以下のraw separation scoreとは別の評価量である。96 / 48 / 32 / 24次元における記述的なstandard-minus-suffix中央値は、+0.002624 / +0.009473 / +0.004026 / +0.009700。Standard-minus-prefixは、+0.022096 / +0.023254 / +0.011040 / +0.025387だった。96次元で正だったのは、それぞれ20 / 36セルと25 / 36セルである。これは事後的・記述的な診断で、推論や同等性の検定ではない。低次元値は同じseedによる代数的な畳み込みである。

実行時の来歴として、matched-null Aの最初のforeground processは、マシン負荷が極端に高い最中、ledger 798行で外部から中断された。Sealを保ったresumeによって、重複・欠損・error・非ゼロのzero-hook RMSなしで14,208行の正確なgridを完了した。この事象は、モデルに関する証拠でも、一般化できる速度の主張でもない。P2、独立ソース、診断runは通常どおり完了した。C1 v1はこれらのrunでは使わなかったが、別に記録した研究文脈への露出により、現在は廃止済みである。

ここにあるのは、再現可能な因果検証前のactivation screening候補と、レイヤーごとに分かれたMilestone 2対照結果である。Glyphの意味、機構、回路、因果経路、トークン化から独立した効果を確立する証拠ではない。運用上のMilestone 2は完了し、layer 2は、将来の新しいversionのbankを使う対象限定型の因果プロトコルを設計できる。C1 v1は別に記録した研究文脈への露出により廃止済みである。Layer 4は未解決のままである。[holdout状態](../docs/HOLDOUT_STATUS.ja.md)も参照する。

## E1探索の読み方

[E1の全結果](../docs/EMOJI_FAMILY_EXPLORATORY_RESULTS.ja.md)は、commit
`0cd4e11610e42253ead9ce9aff9f0b02474a0558`で凍結した、トークン同型な
5 familyの探索実験である。平均transfer行列は両layerで広く正だった。一方、
family等重みのwithin-family超過量は小さく、layer 2で0.014752595564
（95%記述区間[0.002875238085, 0.027439243404]）、layer 4で
0.014887989201（[0.003407563347, 0.019684351979]）だった。Family別区間は、
両layerの全familyで0を含んだ。事前指定したlayer 4のnegative comparatorも
negativeにはならなかった。

Random controlとの比較は不均一だった。Family × layer × seedの30 cell中
10 cellが非正で、layer 2のseed 307とlayer 4のseed 101では、それぞれ
5 familyすべてが該当した。したがって、random controlに対する頑健な優位性は
主張しない。ここで許される解釈は、固定した中間token置換下での探索的な
matched-slot反復と、共有tokenによるtransferが小さなfamily固有超過より
支配的だという範囲に限られる。

Bundle validatorはpassした。Root manifestとは別に公開payload 82件と5つの
role bindingを検証し、hash mismatchとlocal absolute pathはいずれも0だった。
P2/C1 contentが固定済みE1 input surfaceの外にあるというmanifest上の
宣言も検査したが、過去のprocess履歴を独立に完全証明するものではない。
Payloadは1,237,638 byteで、
JSONL 39件・1,635行を含む。Root manifestを含めると83 file、1,303,644 byteで、
manifestのSHA-256は
`c22989ebc9ccaaf5f4652624d61ea11e2a9df4f2148a7886daf50c2fc3e4f53f`である。
省略したraw fileは20件、計74,618,134 byteで、全8,880 intervention rowを含めて
hash、行数、array shapeを対象に応じて記録した。Hashだけでは省略dataを復元できない。

公開エビデンスは次に分かれている。

- [root manifest](EMOJI_FAMILY_EXPLORATORY_V1_MANIFEST.json)
- [tokenizer-only preflight](emoji_family_exploratory_v1/preflight/tokenization_audit_v1.json)
- [解析reportと機械可読出力](emoji_family_exploratory_v1/analysis/report.md)
- [5つの軽量run directory](emoji_family_exploratory_v1/runs/)

E1ではp値も確認的statusも算出していない。絵文字の意味、tokenizer非依存性、
layer固有性、mechanism、因果path、model間の規則性を確立せず、Milestone 2の
判定を更新せず、C1も開かず、Phase I論文gateも満たさない。
