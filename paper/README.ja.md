# GlyphProbe Phase I 論文

[English](README.md) | [凍結済み claim table](CLAIM_TABLE.ja.md)

状態: **匿名manuscriptとcompact evidence archiveをbuild・validate済み。
OpenReview uploadは未実施**。

原稿は NeurIPS 2026 の公式 double-blind workshop style を使い、
Interpretability as a Science workshop の long paper 上限を目標にする。
科学的な統制本文は英語論文である。この日英READMEはbuild、証拠境界、図の
contractを記録するもので、第二の論文ではない。

## ファイル

- `main.tex`: 著者匿名の英語原稿。
- `references.bib`: 初稿で使用する参考文献。
- `neurips_2026.sty` と `checklist_template.tex`: 無改変の公式template
  asset。`checklist.tex`は公式questionを変えず、保守的なdraft answerを入れる。
- `scripts/build_figures.py`: compactかつ検証済みのT19 JSON summaryから図を
  決定論的に生成するscript。
- `scripts/build_anonymous_artifact.py` と
  `scripts/validate_anonymous_artifact.py`: whitelist-onlyで決定論的なarchive
  builderと、integrity/identity境界の独立validator。
- `figures/manifest.json`: 図と同時に生成する入力・出力SHA-256 receipt。
- `ASSET_LICENSES.*`、`COMPUTE_REPORT.*`、`ETHICS_REVIEW.*`: 日英対の
  submission audit。
- `../output/pdf/glyphprobe_t19_first_draft.pdf`: compile済みreview PDF。
- `../output/artifacts/glyphprobe_t19_anonymous_evidence_v0.zip`: standaloneな
  匿名compact artifact。隣にreceiptとSHA-256を置く。

公式formatting archiveは
`https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip`
から取得した。SHA-256は
`82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9`
である。このstyle fileを置くことは、workshop採択や投稿準備完了を意味しない。

無改変のstyleには指定した`dblblindworkshop` optionとworkshop titleが記録される。
一方、匿名submission modeの公式2026 styleはmain-conference footerをhard-codeし、
track nameを使うのはfinal modeだけである。build logではこのlocal
`neurips_2026.sty`が実際にloadされたことを確認した。footerを変えるために公式assetを
patchせず、無改変のまま保持する。

## Build

repository rootから実行する。

```bash
python3 paper/scripts/build_figures.py
SOURCE_DATE_EPOCH=1788307200 tectonic -X compile \
  --outdir "$PWD/paper/build" --outfmt pdf \
  --keep-logs --keep-intermediates --untrusted "$PWD/paper/main.tex"
cp paper/build/main.pdf output/pdf/glyphprobe_t19_first_draft.pdf
python3 paper/scripts/build_anonymous_artifact.py
python3 paper/scripts/validate_anonymous_artifact.py \
  output/artifacts/glyphprobe_t19_anonymous_evidence_v0.zip
```

TectonicはBibTeX passも自動実行する。full TeX Liveがある場合はCodexの
`latex-compile` helperも使用できる。検証したMac buildではTeX Live不在をhelperが
正しく検出したため、bundled Tectonic executableを直接呼び出した。最終copyは、
引用、page count、text extraction、rendered pageを検査した後だけ作る。
`paper/build/` と `tmp/pdfs/` は中間surfaceである。

## 事前指定したclaim境界

論文は異なる判定条件を持つ二つの結果を報告する。raw atomic emojiは、事前指定した
9つすべてのmodel/tokenizer構成で、literal codepoint stringより語彙的に非重複なCLDR
keyword aliasをよくretrieveした。これは4 viewのtoken countを完全一致させた
解析でも成立した。一方、一つのLlama 3.2 3B構成で事前登録したrank-8の後期
component testでは、T19-Lからhold outした評価emoji 192件に対し、jointに必要かつ
十分なprimary `attn_out` / `mlp_out` siteは見つからなかった。表層はT19以前の
研究に現れた可能性がある。

これはtext-only Unicode入力における限定的な語彙対応を支持する。rendered
glyph知覚、人間的な同義語理解、token identity matching、tokenizer非依存性、
pretraining novelty、普遍manifold、完全な回路、scale lawは示さない。許可・除外
する記述は[CLAIM_TABLE.ja.md](CLAIM_TABLE.ja.md)に凍結した。

原稿では、`T19-L`を語彙観察arm、`T19-C`を条件付きcomponent因果armとして初出時に
定義した。Appendix Aには、初期steering screenからT18までの探索→確認の短い経路を
追加した。過去の探索結果と確認失敗は、現在のcontrolが必要になった理由を説明するが、
T19-Lの証拠分母へは加えない。

## 図のchart contract

図はstatic Matplotlib PDFとして出力する。各contractはrender前に、問い、狙う
takeaway、chart family、data sufficiency、renderer、encoding、output、QA義務を
記録する。

### Figure 1 - prospective design

- **問い:** designはどのsurface、語彙endpoint、control、item setを分離するか。
- **Takeaway:** T19-Lはemojiとrepository textでfreshなsymbolを4 text viewと
  組み合わせる。T19-Cは観測基準の通過後だけ、互いに分離したsource / evaluation
  emojiを使う。
- **Family / sufficiency:** annotation付きprocess schematic。事前指定した全armと
  item-set sizeが既知である。
- **Renderer / encoding:** static Matplotlib。観測証拠は青、因果testはorange、
  controlはgrayとし、arrowとlabelでも意味を保持する。
- **Output / QA:** `figures/t19_design.pdf`。全countと判定基準labelを事前指定protocolに
  照合し、paperへ埋め込んだPDFを検査する。

### Figure 2 - modelを跨ぐemoji alias effect

- **問い:** keyword-minus-codepoint top-1は、unrestrictedとtoken-count matchedの
  両方で、事前指定した全構成において正か。
- **Takeaway:** 9構成すべてが正で、登録済み0.02 effect-size floorを超えたが、
  大きさは不均一である。
- **Family / sufficiency:** paired horizontal dot plot。9 model categoryで構成単位の
  exact comparisonに十分である。
- **Renderer / encoding:** static Matplotlib。unrestrictedを青いfilled circle、
  matchedをorangeのopen squareで表す。marker shape、zero line、0.02 dashed lineで
  grayscaleでも読めるようにする。
- **Output / QA:** `figures/t19_model_effects.pdf`。登録済みroster orderを保ち、
  18点を`model_cell_results.json`へ照合し、compile済みpaperのlabelとreference
  lineを検査する。

### Figure 3 - emojiとsymbolの語彙境界

- **問い:** keyword / official-name effectはemojiと非emoji Unicode symbolでどう
  異なるか。
- **Takeaway:** official-name retrievalは広いが、事前指定emoji panelではkeyword
  retrievalがより強く一貫する。symbol contrastはsecondaryかつ非exchangeableの
  ままである。
- **Family / sufficiency:** 9 modelにわたる2 panel paired dot plot。語彙endpoint
  ごとに1 panelとする。
- **Renderer / encoding:** static Matplotlib。emojiは青circle、symbolはgray
  diamond、unrestricted / matchedはfilled / open markerとline styleで分ける。
- **Output / QA:** `figures/t19_emoji_symbol_boundary.pdf`。36個のmodel-level valueを
  検証し、x-axisを共通化し、"registered secondary"と明示してcaptionとlegendを
  検査する。

### Figure 4 - component-level causal test

- **問い:** random-adjusted necessityとsufficiencyがともに0.02のfloorを超える
  事前指定siteはあるか。
- **Takeaway:** 両componentを通過したsiteはない。block-27 MLPはsecondaryな
  sufficiency-only asymmetryであり、完全mediatorではない。
- **Family / sufficiency:** 2 panel horizontal interval dot plot。登録済み6 siteを
  95% item-bootstrap interval付きで全表示する。
- **Renderer / encoding:** static Matplotlib。necessityはcircle、sufficiencyは
  square、二つのprimary block-24 siteは濃いoutline、secondaryはgrayで表す。
- **Output / QA:** `figures/t19_causal_sites.pdf`。12 estimateとintervalを
  `causal_site_results.json`へ照合し、zero / 0.02 referenceを表示し、primary site
  の強調を検査する。

### Figure 5 - 探索から確認へ至る系譜

- **問い:** T19のdesignへ至るまでに、どの先行結果が次の判断を変えたか。
- **Takeaway:** token構造と持続性の研究がendpointを絞り、後続の語彙・因果研究が
  二つのarmを持つdesignを導いた。先行stageはT19-L primaryの証拠分母に入らない。
- **Family / sufficiency:** annotation付きdecision lineage。T1--T19を五つのstageへ
  まとめ、系列を証拠の累積として扱わない。
- **Renderer / encoding:** static Matplotlib。token・持続性diagnosticはgray、
  語彙・boundary研究はblue、T19はorangeで表す。
- **Output / QA:** `figures/t19_lineage.pdf`。全study labelをAppendix Aへ照合し、
  compile済みpaperでbox labelとarrowを検査する。

## 残るsubmission境界

- reproducibility、open access、compute checklistは`No`のまま。compact artifactは
  model-dependent raw arrayと完全なintervention ledgerを含まず、T19 acquisitionの
  duration/peak memoryもreceipt-boundでない。
- double-blind copyの凍結後にだけauthor listとacknowledgmentsを確定する。
- OpenReview recordを検証できるだけ早くuploadする。

Data/codeのopen accessへの回答は、**N/AではなくNo**である。公式checklistで
N/Aが許されるのは、codeを要する実験を含まないpaperである。査読後の公開予定だけでは
submission時点の回答は変わらない。新archiveは匿名compact auditとdocumentation gapを
閉じたが、exact raw replayまでは閉じていない。License、ethics、new-asset documentation、
保守的なLLM-assistance declarationは完了した。
