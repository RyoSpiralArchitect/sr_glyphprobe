# Llama 3.2 3B MPS絵文字transport v1 証拠

[English](README.md) · [プロトコル](../../docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1.ja.md) · [ホールドアウトの状態](../../docs/HOLDOUT_STATUS.ja.md)

このdirectoryは、別versionとして定義したE2 Transformers/MPS FP32
transport studyの公開証拠rootである。Static freezeの時点では、この英日案内だけを
置く。その後、model forwardを伴わないpreflightにより、実行前のrepository変更を
`preflight/tokenization_audit_v1.json`だけに限定して追加できる。

固定した10 cellがすべて完走し、検証に合格した場合に限り、no-overwriteの公開builderが
compactな`runs/`と完全な`analysis/`を追加する。公開bundleでは、各local runの
`interventions.jsonl`、`source_activations.npz`、`directions.npz`、
`target_baselines.npz`を意図的に除外する。Root manifestは、除外した各fileの
SHA-256、byte数、row数またはarray metadataを記録し、公開memberすべてをhashで
固定する。完全なlocal run directoryは、再実行を検証するための権威ある証拠として残す。

本studyでは、探索済みのprestage target 24件を再利用する。P2と廃止済みC1 v1は
使わない。絵文字の意味、tokenizer非依存性、独立targetによる確認、因果、backendの
切り分け、model scaleへの一般化は確立できない。`analysis/`が存在しない場合、
有効な科学的結果はまだ公開されていない。
