# GlyphProbe T19/T20/T21 匿名evidence artifact v4

[English](README.md)

この**compactなdouble-blind review artifact**は、事前指定したT19/T20/T21プロトコル、
選択済み項目集合、compactな結果、独立検証報告、解析・検証コード、論文ソース、図、
匿名review PDFを結び付ける。T19-Lの主要区間の統計、T21-Cの同時推論、事後的なT21
マージン分解をモデルなしで再計算できる。raw dataからの再実行には下記の追加ファイルが必要。

v4は、論文だけを読んだ読者の指摘を受けて原稿・引用・日英の主張文書を更新した版である。
記載したT21基準正答率を既存の条件別平均に照合する、読み取り専用の回帰テストを追加した。
実験結果・統計判定は不変で、この文章改訂のための新規収集や統計の再計算は行っていない。

## 最初に検証する

zip自体は隣接する`.sha256` fileとSHA-256を照合する。展開後、artifact rootで次を
実行する。

```bash
python3 scripts/validate_anonymous_artifact.py .
```

validatorは、完全なentry roster、全payloadのSHA-256/byte count、`SHA256SUMS`、安全な
relative path、固定archive timestamp、禁止raw/model file type、保守的なauthor identity・
local path tokenを検査する。passが示すのはpackage integrityとomission policyであり、
scientific estimandの正しさではない。

## 含むもの

- `paper/glyphprobe_t19_anonymous.pdf`と匿名TeX/BibTeX source。
- 決定論的なpaper figure 7件と入出力のhash manifest、箱内ラベルのレイアウト回帰テスト。
- T19-L selection、freeze、config、tokenizer preflight、compact observational result、
  独立validation receipt、全9モデルの主要区間の予測indexと正確なstratum。
- T19-C go manifest、compact component result、独立validation receipt。
- T19-Cの事後的な全状態交換についての記述的結果。
- T20-Cの設定、項目選択、事前指定と実行承認のmanifest、事前検査、訓練・評価報告、
  compactな結果、独立validation receipt、査読後のチェックポイント採用検証。
- T21のpilotと別のprospective確認計画、露出済み項目によるcanaryのreceipt、収集・解析報告、
  別実装による数値検証、確認用195項目すべての派生スカラー比較値、事後分解と明記した
  自項目・競合のマージン成分。
- receipt生成方法を点検するためのexecutor、analyzer、independent validator source。
- T19 freezeが参照する最小限のT9/T10/T18 binding。
- 日英対のclaim、license、compute、ethics、protocol、result、artifact-boundary文書。
- 新規code向けApache License 2.0と、Unicode/CLDR派生行向けUnicode License v3 notice。

`ARTIFACT_MANIFEST.json`がmachine-readableな境界であり、全payloadのpath、size、digestを
列挙する。`SHA256SUMS`はmanifest自体も追加でbindする。
固定の`reproducibility_timestamp_utc`とZIP timestampは、決定論的な梱包のための値であり、
build時刻や実験時刻ではない。実際の設計・収集・解析時刻は各実験receiptに残す。

## 意図的に除外するもの

- model weight、tokenizer file、cache、virtual environment、secret。
- T19/T20/T21のmodel-dependent activation array、causal source subspace、causal evaluation
  array、完全なintervention ledger。
- Git metadata、repository remote、author metadata、local absolute path、privateな
  execution-host情報。
- T19 evidence denominatorに入らない探索raw output。

除外したraw arrayは同梱acquisition/validation receiptでbindされるが、このcompact package
だけでは独立replayできない。compact-result/figure audit、予測indexからのT19-L再計算、
派生比較値からのT21-C統計再計算、事後的scalar分解、source-code inspection、
manuscript verificationは可能だが、upstream model assetを別途取得しない
完全reacquisitionや、compact evidenceだけからのraw-array再構成はできない。

## Compact surfaceを再生成する

integrity validatorはPython standard libraryだけを使う。scientific Python file向けの
記録済みacquisition stackは`paper/COMPUTE_REPORT.md`、小さなaudit/figure環境は
`requirements-audit.txt`にある。

T19-Lの主要区間の全36 randomization検定・記述的区間、モデル判定、model横断primaryは
NumPyだけで再計算できる。

```bash
python3 scripts/validate_t19_compact_predictions_v0.py \
  --compact validation/t19_lexical_alias_unicode_control_v0/compact_v0/predictions.json
```

各検定は19,999回の置換、各区間は20,000回の項目bootstrapを使う。matched帰無分布は
正確なstratum内で置換し、`1/n`という一様当て推量の基準とは区別する。
採用emoji数は31–51項目である。

T21-Cの5比較の同時下限、判定、記述的なtop-1平均は、NumPyだけで再計算できる。

```bash
python3 scripts/validate_t21_compact_inference_v0.py \
  --compact validation/t21_glyph_context_path_confirmation_v0/results/item_contrasts.json \
  --result validation/t21_glyph_context_path_confirmation_v0/results/confirmation_result.json
```

項目の再標本化indexを共有するbootstrapを20,000回再計算する。一致が検証するのは、
同梱スカラー値からの統計計算である。モデル状態への介入が正しく実装されたことは、
receiptに結び付いた別の検証として扱う。

同梱scalarから事後的なT21分解を検証する。

```bash
python3 scripts/validate_t21_margin_decomposition_v0.py \
  --decomposition validation/t21_margin_decomposition_v0/decomposition.json \
  --original validation/t21_glyph_context_path_confirmation_v0/results/item_contrasts.json
```

自項目keywordから最大競合を引いた対比を元の195項目のマージン行と照合し、記述的平均を
再計算する。成分の有意差検定は追加せず、元のマージン下限を各成分には適用しない。
[査読後レポート](docs/POST_REVIEW_EVIDENCE_RESULTS_V0.ja.md)では、T20の採用時点と
step 600の訓練診断の違いも説明する。

disposableな展開copyでfigureを再生成する。

```bash
python3 paper/scripts/build_figures.py
python3 scripts/validate_anonymous_artifact.py .
```

二つ目のcommandは、再生成が記録済みfigure/manifest hashとbyte単位で一致した場合だけpassする。
fontやrendering library差でplot値が同じでもPDF/PNG byteは変わりうるため、不一致は
rendering parity結果であり、自動的にscientific discrepancyとはしない。

paper sourceをcompileする場合は、`paper/README.md`にURL/SHA-256を記録したNeurIPS 2026
公式formatting archiveを取得し、`neurips_2026.sty`を`main.tex`の隣へ置いて実行する。

```bash
mkdir -p paper/build
SOURCE_DATE_EPOCH=1788307200 tectonic -X compile --outdir paper/build --outfmt pdf \
  --keep-logs --keep-intermediates --untrusted paper/main.tex
```

conference style fileはここでは意図的に再配布しない。同梱PDFがartifactの統制rendered
manuscriptである。

## Claim境界

T19-Lは、固定text-only Unicode入力とexact token-count control下での限定的なmodel横断
lexical retrievalを支持する。T19-Cは一つのLlama 3.2 3B構成で、登録済みnecessity・
sufficiencyを両方通る事前指定の主要late componentを見つけなかった。
T20-Cの主要サイトは登録済み規則の下で較正不能となった。その全状態交換の非対称性から、
別のT21研究を設計した。T21-Cは、Llama 3.2 3Bの一構成でblock 21のreadoutをresetした後、
glyph位置のkeyとvalueが連続的な語彙検索marginへ寄与することを条件付きで支持する。
事前指定した5比較は、同時信頼下限がすべて正だった。絶対的なnecessityとrescueのtop-1
平均効果は、ともにゼロである。T19/T20の判定規則は変更せず、正答率向上、無条件または
emojiに特有の経路、完全な媒介機構は示さない。
rendered-glyph perception、
人間的意味、tokenizer independence、universal manifold、完全circuit、scale law、
model-population generalityは示さない。
