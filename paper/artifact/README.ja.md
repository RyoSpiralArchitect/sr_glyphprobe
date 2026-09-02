# GlyphProbe T19/T20 匿名evidence artifact v1

[English](README.md)

この**compactなdouble-blind review artifact**は、事前指定したT19/T20プロトコル、
選択済み項目集合、compactな結果、独立検証報告、解析・検証コード、論文ソース、図、
匿名review PDFを結び付ける。raw dataからの再実行には、下記の追加ファイルが必要になる。

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
- 決定論的なpaper figure 6件と入出力のhash manifest、箱内ラベルのレイアウト回帰テスト。
- T19-L selection、freeze、config、tokenizer preflight、compact observational result、
  独立validation receipt。
- T19-C go manifest、compact component result、独立validation receipt。
- T19-Cの事後的な全状態交換についての記述的結果。
- T20-Cの設定、項目選択、事前指定と実行承認のmanifest、事前検査、訓練・評価報告、
  compactな結果、独立validation receipt。
- receipt生成方法を点検するためのexecutor、analyzer、independent validator source。
- T19 freezeが参照する最小限のT9/T10/T18 binding。
- 日英対のclaim、license、compute、ethics、protocol、result、artifact-boundary文書。
- 新規code向けApache License 2.0と、Unicode/CLDR派生行向けUnicode License v3 notice。

`ARTIFACT_MANIFEST.json`がmachine-readableな境界であり、全payloadのpath、size、digestを
列挙する。`SHA256SUMS`はmanifest自体も追加でbindする。

## 意図的に除外するもの

- model weight、tokenizer file、cache、virtual environment、secret。
- T19/T20のmodel-dependent activation array、causal source subspace、causal evaluation
  array、完全なintervention ledger。
- Git metadata、repository remote、author metadata、local absolute path、privateな
  execution-host情報。
- T19 evidence denominatorに入らない探索raw output。

除外したraw arrayは同梱acquisition/validation receiptでbindされるが、このcompact package
だけでは独立replayできない。したがって、exact compact-result/figure audit、source-code
inspection、manuscript verificationは可能だが、upstream model assetを別途取得しない
完全reacquisitionや、compact evidenceだけからのraw-array再構成はできない。

## Compact surfaceを再生成する

integrity validatorはPython standard libraryだけを使う。scientific Python file向けの
記録済みacquisition stackは`paper/COMPUTE_REPORT.md`、小さなaudit/figure環境は
`requirements-audit.txt`にある。

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
T20-Cの主要サイトは登録済み規則の下で較正不能となった。全状態交換はglyph位置の
文脈から回復する経路の仮説を動機づけるが、その経路の同定や全rankの排除を示さない。
rendered-glyph perception、
人間的意味、tokenizer independence、universal manifold、完全circuit、scale law、
model-population generalityは示さない。
