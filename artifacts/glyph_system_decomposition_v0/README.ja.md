# T11 glyph-system decomposition atlas 証拠束

[English](README.md) · [結果の解釈](../../docs/GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.ja.md) · [凍結protocol](../../docs/GLYPH_SYSTEM_DECOMPOSITION_V0.ja.md)

このディレクトリには、T11 discovery atlasの公開用証拠を、監査に必要な範囲へ絞って収めている。結果は探索的であり、判定は**留保付き共有可能**である。T10の結論は変わらない。意味、因果、tokenizer非依存性、scale law、tuning効果、architecture一般性、model一般性も主張しない。

## 収録内容

- `analysis/analysis.json`：9 cellの文脈集計、入力receiptとの対応、分散分解、claim boundary
- `analysis/cross_model_geometry.jsonl`：記述的なgeometry 1,040行
- `analysis/cross_model_item_margin_agreement.jsonl`：model pairごとのitem-margin一致度 720行
- `validation/independent_validation.json`：別実装で再計算した主要表と入力binding
- 各subdirectoryとbundle rootのSHA-256 ledger
- `PUBLIC_MANIFEST.json`：収録payload、省略したcompact table、外部summary/runとの対応、raw archiveの省略を記録したmanifest

独立validatorでは、保存済みitem-marginのcell中央値32,736件、model横断agreement 720行、三要因分散分解7件、depth trajectory 2,592行を再計算し、不一致はゼロだった。Model横断activation geometryはhashとschemaまで検査したが、再構築には省略したraw activation archiveが必要なため、独立再計算の対象外としている。

## 省略したデータ

Broad cell table 1,008行、depth cell table 2,592行、depth trajectory table 2,592行はGitへ入れていない。各ファイルのhashとbyte数はpublic manifestに残した。9 model分のitem-margin NPZ、acquisition run、model cache、約9.15 GiBのdense FP32 activationもGit外に置いている。Hashは省略データとの対応を固定するが、データそのものを復元するものではない。

したがって、このbundleだけで報告した集計patternと独立compact validationは監査できる。一方、raw vectorからactivation-geometry rowを再構築するには、炉側archiveが別途必要となる。

## 凍結した境界

T11では、T10と同じ9 model/tokenizer cellを使い、取得対象843件に73,566回のmodel forwardを行った。解析工程で追加したmodel forwardはゼロ。Reserve 268件はすべて未forwardで、model outcomeも未観測のままである。Reserveを開く前に、T12でendpointを一つに絞り、multiplicity familyとともに別途凍結しなければならない。
