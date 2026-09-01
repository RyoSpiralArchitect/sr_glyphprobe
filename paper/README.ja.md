# GlyphProbe Phase I 論文

[English](README.md) | [凍結済み claim table](CLAIM_TABLE.ja.md)

状態: **英語初稿をcompileして凍結済みであり、まだ投稿可能ではない**。

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
- `figures/manifest.json`: 図と同時に生成する入力・出力SHA-256 receipt。
- `../output/pdf/glyphprobe_t19_first_draft.pdf`: compile済みreview PDF。

公式formatting archiveは
`https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip`
から取得した。SHA-256は
`82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9`
である。このstyle fileを置くことは、workshop採択や投稿準備完了を意味しない。

## Build

repository rootから実行する。

```bash
python3 paper/scripts/build_figures.py
tectonic -X compile --outdir "$PWD/paper/build" --outfmt pdf \
  --keep-logs --keep-intermediates --untrusted "$PWD/paper/main.tex"
cp paper/build/main.pdf output/pdf/glyphprobe_t19_first_draft.pdf
```

TectonicはBibTeX passも自動実行する。full TeX Liveがある場合はCodexの
`latex-compile` helperも使用できる。検証したMac buildではTeX Live不在をhelperが
正しく検出したため、bundled Tectonic executableを直接呼び出した。最終copyは、
引用、page count、text extraction、rendered pageを検査した後だけ作る。
`paper/build/` と `tmp/pdfs/` は中間surfaceである。

## 凍結した初稿のclaim境界

論文の中心は解離である。raw atomic emojiは、9つすべての凍結済み
model/tokenizer cellで、literal codepoint stringより語彙的に非重複なCLDR
keyword aliasをよくretrieveした。これは4 viewのtoken countを完全一致させた
解析でも成立した。一方、一つのLlama 3.2 3B cellで事前登録したrank-8の後期
component testでは、未使用の評価emoji 192件に対し、jointに必要かつ十分な
primary `attn_out` / `mlp_out` siteは見つからなかった。

これはtext-only Unicode入力における限定的な語彙対応を支持する。rendered
glyph知覚、人間的な同義語理解、token identity matching、tokenizer非依存性、
pretraining novelty、普遍manifold、完全な回路、scale lawは示さない。許可・除外
する記述は[CLAIM_TABLE.ja.md](CLAIM_TABLE.ja.md)に凍結した。

## 図のchart contract

図はstatic Matplotlib PDFとして出力する。各contractはrender前に、問い、狙う
takeaway、chart family、data sufficiency、renderer、encoding、output、QA義務を
記録する。

### Figure 1 - prospective design

- **問い:** designはどのsurface、語彙endpoint、control、data bankを分離するか。
- **Takeaway:** T19-Lはemojiとrepository textでfreshなsymbolを4 text viewと
  組み合わせる。T19-Cは観測gate通過後だけ、互いに分離したsource / evaluation
  emojiを使う。
- **Family / sufficiency:** annotation付きprocess schematic。凍結した全armとbank
  sizeが既知である。
- **Renderer / encoding:** static Matplotlib。観測証拠は青、因果testはorange、
  controlはgrayとし、arrowとlabelでも意味を保持する。
- **Output / QA:** `figures/t19_design.pdf`。全countとgate labelを凍結protocolに
  照合し、paperへ埋め込んだPDFを検査する。

### Figure 2 - modelを跨ぐemoji alias effect

- **問い:** alias-minus-codepoint top-1は、unrestrictedとtoken-count matchedの
  両方で、すべての凍結cellにおいて正か。
- **Takeaway:** 9 cellすべてが正で、事前登録した0.02の実用floorを超えたが、
  大きさは不均一である。
- **Family / sufficiency:** paired horizontal dot plot。9 model categoryでcell単位の
  exact comparisonに十分である。
- **Renderer / encoding:** static Matplotlib。unrestrictedを青いfilled circle、
  matchedをorangeのopen squareで表す。marker shape、zero line、0.02 dashed lineで
  grayscaleでも読めるようにする。
- **Output / QA:** `figures/t19_model_effects.pdf`。登録済みroster orderを保ち、
  18点を`model_cell_results.json`へ照合し、compile済みpaperのlabelとreference
  lineを検査する。

### Figure 3 - emojiとsymbolの語彙境界

- **問い:** alias / canonical-name effectはemojiと非emoji Unicode symbolでどう
  異なるか。
- **Takeaway:** canonical-name retrievalは広いが、凍結emoji panelではalias
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
  凍結siteはあるか。
- **Takeaway:** 両componentを通過したsiteはない。block-27 MLPはsecondaryな
  sufficiency-only asymmetryであり、完全mediatorではない。
- **Family / sufficiency:** 2 panel horizontal interval dot plot。登録済み6 siteを
  95% item-bootstrap interval付きで全表示する。
- **Renderer / encoding:** static Matplotlib。necessityはcircle、sufficiencyは
  square、二つのprimary block-24 siteは濃いoutline、secondaryはgrayで表す。
- **Output / QA:** `figures/t19_causal_sites.pdf`。12 estimateとintervalを
  `causal_site_results.json`へ照合し、zero / 0.02 referenceを表示し、primary site
  の強調を検査する。

## Draft v0で見えている投稿gap

- anonymous artifactに関する記述をdouble-blind archiveへ置き換えるか、未提供の
  理由を明記する。
- 現在のchecklistに明示した`No` / `N/A`のsubmission gapを解消する。
- manuscript中の全数値をcompact receiptへ独立照合する。
- double-blind copyの凍結後にだけauthor listとacknowledgmentsを確定する。
- OpenReview recordを検証できるだけ早くuploadする。
