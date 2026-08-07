# Llama 3.2 3B MPS emoji-transport v2 エビデンス

[English](README.md) · [プロトコル](../../docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.ja.md) · [ホールドアウト状況](../../docs/HOLDOUT_STATUS.ja.md)

プロトコル ID: `glyphprobe-e2-llama32-3b-mps-emoji-transport-v2`

このディレクトリは、v2 研究のために別バージョン化した公開エビデンスの
ルートです。v1 はモデル forward 0 回の preflight 失敗記録として不変に
保ちます。v2 で変えるのは、修正した tokenizer audit と、新しい試行を独立
させるための protocol、receipt、run、analysis、log、publication の全名前
空間だけです。

static freeze 時点の payload は、この英日 README の 2 ファイルだけです。
モデル forward 0 回の preflight が通過した場合に限り、
`preflight/tokenization_audit_v2.json` を追加します。10 個の独立 process と
6 ファイルの analysis がすべて完了した場合に限り、最終 compact bundle を
追加できます。

完成した公開 bundle は、各 local run の厳密な 19 ファイルから 15 ファイル
をコピーします。`interventions.jsonl`、`source_activations.npz`、
`directions.npz`、`target_baselines.npz` は意図的に除外し、root manifest に
SHA-256、byte 数、JSONL または NPZ の構造 inventory を記録します。除外した
10 個の intervention ledger は合計 15,600 行です。local run path を含む
launcher log も公開しません。

root manifest は、この英日ペア、v2 publication adapter 2 本、その不変な v1
base script 依存、v2 analyzer、v2 freeze manifest、preflight、execution
receipt、analysis、およびコピーした全 run member を hash で拘束します。
builder と独立 validator は絶対 filesystem path と非同一 overwrite を拒否
します。

24 target は再利用した探索用 prestage target です。保護対象の
`p2_confirmatory_targets_v1.jsonl` と `c1_causal_holdout_targets_v1.jsonl` は
宣言にのみ現れます。publication tool はその内容を入力として受け取らず、
open、read、hash、tokenize、model forward のいずれも行いません。

このエビデンスが支えられるのは、protocol に定めた Transformers/MPS 上の
限定的な探索的主張だけです。emoji semantics、tokenizer independence、独立
target confirmation、causal localization、backend replication、model-scale
effect は確立しません。
