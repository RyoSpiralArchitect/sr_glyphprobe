# 公開エビデンス・バンドル

[English](README.md)

GlyphProbe初回リリースのうち、個人環境のパスを除いた軽量な検証資料を収録しています。

- `mlx_gpt2_parity/receipt.json`：固定GPT-2 FP32でのMLX対Transformers/MPSパリティ・速度ゲート
- `v1_standard_mlx/`：完了runのレシート、各種要約、軽量な診断表、レポート、独立artifact監査
- `MANIFEST.json`：収録ファイルのSHA-256と、Gitから除外した大容量ローカルartifactのhash

77,327,172 byteの条件ledgerと3つのNPZ配列は収録していません。hashで監査対象だったローカルartifactは特定できますが、欠けたデータを復元することはできません。完全なledgerが必要な場合はrunを再現してください。

ここにあるのは、再現可能な「因果検証前のactivation screening候補」です。glyphの意味、回路、因果経路を確立した証拠ではありません。
