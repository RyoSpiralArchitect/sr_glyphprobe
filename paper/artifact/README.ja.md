# GlyphProbe T19 匿名evidence artifact v0

[English](README.md)

これは**compactなdouble-blind review artifact**であり、完全なopen-data再現を
主張するものではない。凍結T19 protocol、選択済みitem bank、compact result、独立
validation receipt、analysis/validator code、paper source、figure、匿名review PDFを
結び付ける。

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
- 決定論的なpaper figure 4件とinput/output hash manifest。
- T19-L selection、freeze、config、tokenizer preflight、compact observational result、
  独立validation receipt。
- T19-C go manifest、compact component result、独立validation receipt。
- receipt生成方法を点検するためのexecutor、analyzer、independent validator source。
- T19 freezeが参照する最小限のT9/T10/T18 binding。
- 日英対のclaim、license、compute、ethics、protocol、result、artifact-boundary文書。
- 新規code向けApache License 2.0と、Unicode/CLDR派生行向けUnicode License v3 notice。

`ARTIFACT_MANIFEST.json`がmachine-readableな境界であり、全payloadのpath、size、digestを
列挙する。`SHA256SUMS`はmanifest自体も追加でbindする。

## 意図的に除外するもの

- model weight、tokenizer file、cache、virtual environment、secret。
- T19のmodel-dependent activation array、causal source subspace、causal evaluation
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

二つ目のcommandは、再生成が凍結figure/manifest hashとbyte単位で一致した場合だけpassする。
fontやrendering library差でplot値が同じでもPDF/PNG byteは変わりうるため、不一致は
rendering parity結果であり、自動的にscientific discrepancyとはしない。

paper sourceをcompileする場合は、`paper/README.md`にURL/SHA-256を記録したNeurIPS 2026
公式formatting archiveを取得し、`neurips_2026.sty`を`main.tex`の隣へ置いて実行する。

```bash
tectonic -X compile --outdir paper/build --outfmt pdf \
  --keep-logs --keep-intermediates --untrusted paper/main.tex
```

conference style fileはここでは意図的に再配布しない。同梱PDFがartifactの統制rendered
manuscriptである。

## Claim境界

T19-Lは、固定text-only Unicode入力とexact token-count control下での限定的なmodel横断
lexical retrievalを支持する。T19-Cは一つのLlama 3.2 3B cellで、登録済みnecessity・
sufficiencyを両方通る凍結primary late componentを見つけなかった。rendered-glyph perception、
人間的意味、tokenizer independence、universal manifold、完全circuit、scale law、
model-population generalityは示さない。
