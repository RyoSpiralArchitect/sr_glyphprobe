# GlyphProbe Phase I 論文

[English](README.md) | [今回の主張](CURRENT_CLAIMS_20261015.ja.md) | [改訂記録](REVISION_NOTES_20261015.ja.md) | [過去の主張](CLAIM_TABLE.ja.md)

2026-10-26時点: **公開論文は10月15日の独立プレプリント・Version 1.0.0のままであり、
元の研究リポジトリも現在public**。
[最新版PDF](../output/pdf/glyphprobe_preprint_20261015.pdf) ·
[公開資料の案内](PUBLIC_RELEASE_20261015.ja.md) ·
[ライセンスの範囲](PUBLIC_LICENSES_20261015.ja.md) ·
[フレッシュアイ査読と対応](FORK_REVIEW_PUBLICATION_20261015.ja.md)。
[Zenodo公開記録・DOI `10.5281/zenodo.23376699`](https://zenodo.org/records/23376699)で、
2026年10月15日付のVersion 1.0.0をオープンなプレプリントとして公開した。
公開対象を絞った[sr_glyphprobe-public](https://github.com/RyoSpiralArchitect/sr_glyphprobe-public)
も引き続き利用できる。元の[sr_glyphprobe](https://github.com/RyoSpiralArchitect/sr_glyphprobe)
も現在**public**である。10月26日の統合では、未公開の開発履歴を丸ごと移さず、点検済みの
研究ファイルを追加する。[統合範囲](../docs/PUBLIC_INTEGRATION_SCOPE_20261026.ja.md)と
[次版のテーマ案](../docs/PAPER_NEXT_THEME_20261026.ja.md)を参照。テーマ案は新しい結果ではなく、
固定済みT22の384項目設計も変更しない。著者の個別回答、割当、保護holdout、運用上の引き継ぎ、
機械固有の生のruntime記録は今回の統合から除外する。この範囲の点検は、元から存在する全commitや
成果物の公開可否を認証するものではない。
アーカイブとmanifestは公開前の準備時点の記録を変更せず保持する。その後に別途確認した
公開状態は、Zenodoの公開記録とこの更新可能なREADMEに記し、準備記録を遡って書き換えない。
9月の原稿と匿名資料は過去の成果物として保存しており、10月の文脈実験や読み出しの適格性検査は含まない。
[実験の読み方](EXPERIMENT_GUIDE.ja.md)と
[改訂・公開の計画](../docs/POST_REVIEW_REVISION_20261007.ja.md)を参照。
改訂PDFは過去の結果、文脈に応じた応答の測定、著者による試用の集計を保持する。
さらに、明示された報告だけを扱う事前指定のテキスト実験で、絵文字解釈へ進む前に測定方法を検査する。
過去の確認実験、文脈実験の開発、有限集合での読み出し適格性検査は、主張できる範囲を分ける。
独立した意味の検証と応答への因果効果は未解決。
[研究の再考ノート](../docs/CONTEXTUAL_EMOJI_REASSESSMENT_20261010.ja.md)を参照。
著者は今回の論文・独自の論文図・新たな公開用データへのCC BY 4.0の適用を承認した。
コードと通常のプロジェクト文書はApache 2.0を維持し、第三者資料と過去の成果物の元の
権利表示も保持する。[公開資料の案内](PUBLIC_RELEASE_20261015.ja.md)で準備と公開を区別し、
収録する証拠と除外物を示す。

NeurIPS 2026 workshop **Interpretability as a Science (InterpScience)**で受けた
査読コメントをもとに改訂したプレプリントであり、workshop採択論文やproceedings掲載論文ではない。

10月15日の適格性検査は**4,640/4,640 forwardを完了**し、数値の受入検査と別実装による保存値の検証を
通過した。一方、事前指定した科学的な要件は満たさなかった。直接質問・最小回答は保留検査で
**88/96正答**（誤答4、同点4、全条件が正しい課題は8/16）、直接質問の二つのA/B対応は
**104/192正答、同点19**だった。全形式・失敗・分母を論文と公開用集計に保持する。
指定した有限の実験を完了したものであり、意味や通常の出力への因果効果を測る道具として
適格になったという主張はしない。

現在の原稿は標準の`article`、`geometry`、Times系本文フォント、`natbib`を使い、
NeurIPS styleと投稿用チェックリストを読み込まない。簡潔な共創謝辞には役割と資料の由来に
関する限界を残し、会議規定の定型文を外した。今回の書式・公開資料の改訂で科学的結果を
変更しておらず、会議採択も主張しない。
科学的な統制本文は英語論文である。この日英READMEはbuild、証拠境界、図の
contractを記録するもので、第二の論文ではない。

## ファイル

- `main.tex`: 著者名を記した英語の独立プレプリント。
- `references.bib`: 初稿で使用する参考文献。
- `neurips_2026.sty`、`checklist_template.tex`、`checklist.tex`: 保存した過去のworkshop用資料。
  現在の原稿はいずれにも依存しない。
- `scripts/build_figures.py`: compactかつ検証済みのT19/T20/T21 JSON summaryから図を
  決定論的に生成するscript。
- `scripts/build_anonymous_artifact.py` と
  `scripts/validate_anonymous_artifact.py`: whitelist-onlyで決定論的なarchive
  builderと、integrity/identity境界の独立validator。
- `figures/manifest.json`: 図と同時に生成する入力・出力SHA-256 receipt。
- `ASSET_LICENSES.*`、`COMPUTE_REPORT.*`、`ETHICS_REVIEW.*`: 日英対の
  submission audit。
- `contextual_development_20261010.tex`: 文脈測定の記述的な補遺。
- `contextual_input_examples_20261015.tex`: 公開入力と候補文の全文例。
- `readout_qualification_20261015.tex`: 明示された報告を使う適格性検査の設計と結果。
- `generated/contextual_development_tables_20261010.tex`: 集計のみを含む表。
  `scripts/build_development_summary_20261010.py`で生成し、手では編集しない。
- `../validation/contextual_emoji_working_revision_20261010/summary.json`:
  再確認した集計と由来。著者の個別記録は含めない。
- `../output/pdf/glyphprobe_preprint_20261015.pdf`: 公開済みの独立プレプリントそのもの。
- `../output/pdf/glyphprobe_t19_first_draft.pdf`: 保存した9月のreview PDF。
- `../artifacts/public_release_20261015/historical/glyphprobe_t19_anonymous_evidence_v4.zip`:
  公開payload内にbyte単位で保持した9月のcompact資料。
- `PUBLIC_RELEASE_20261015.ja.md`と`PUBLIC_LICENSES_20261015.ja.md`: 今回の公開範囲、
  ライセンス、除外物、配布資料だけを使った再計算方法。
- `../output/artifacts/glyphprobe_public_release_20261015_v2.zip`: 公開済みVersion 1.0.0の資料そのもの。
  公開前の準備記録は変更せず保持する。
- `../artifacts/public_release_20261015/`: 公開payloadを変更せず展開したもの。
  正確な収録一覧を`ARTIFACT_MANIFEST.json`と`SHA256SUMS`で固定する。
- `../artifacts/public_release_20261015/evidence/readout_qualification_v1/specification.public.json`:
  入力・実行条件の公開用投影。同じdirectoryに完全な保存得点と元記録への対応を収録する。
- `RELEASE_CANDIDATE_20261015.ja.md`: 旧候補版の案内。元のbuild・再計算パスは手元の
  取得archiveを必要とし、公開資料を検証する入口ではない。

10月7日・10日・15日の中間PDFと旧候補ZIPは今回の統合には含めない。適格性検査の生の
specification・run directoryと、機械固有の取得記録も除外する。それらへの過去の参照は
著者の手元のarchiveを記述したもので、公開読者が再構成したり検査を迂回したりすべき前提では
ない。公開用投影と下記の検証コマンドを用いる。他の選択済み科学的ファイルも部分的な証拠であり、
全runの数値再計算に必要な完全な資料一式ではない。

過去の公式formatting archiveは
`https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip`
から取得した。SHA-256は
`82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9`
である。このstyle fileを置くことは、workshop採択や投稿準備完了を意味しない。

9月の投稿は`dblblindworkshop`、10月の旧候補版は`preprint`を使用した。現在の独立論文は
どちらのmodeもstyleも使わず、投稿用チェックリストも含めない。過去の公式style自体は
無改変のまま保持する。以下のコマンドでは過去のPDFと添付資料を再生成しない。

## Build

repository rootから実行する。

```bash
tectonic -X compile \
  --outdir "$PWD/paper/build/public_preprint_20261015" --outfmt pdf \
  --keep-logs --keep-intermediates --untrusted "$PWD/paper/main.tex"
cp -n paper/build/public_preprint_20261015/main.pdf output/pdf/glyphprobe_preprint_20261015.pdf
```

TectonicはBibTeX passも自動実行する。検証したMacではbundled executableを
直接使うか、Codexの`latex-compile` helperに`--compiler tectonic`を指定する。
helperの自動選択は文献処理をTeX Live向けと判定するが、この端末にはTeX Liveはない。
最終copyは、
引用、page count、text extraction、rendered pageを検査した後だけ作る。
`paper/build/` と `tmp/pdfs/` は中間surfaceである。

既存の図は変更せず保持する。この論文のbuildには確認済みの公開集計と生成済みの表で足りる。
人の個別回答数を再計算するには公開範囲から除外した記録が必要であり、ここで案内する手順には
含めない。過去のfull-run検査を通すために、個別回答、生のruntime記録、運用上の引き継ぎを
取り込まない。

## 公開済み保存得点の検証

リポジトリrootから、Python標準ライブラリだけで実行できる。

```bash
python3 -B artifacts/public_release_20261015/paper/scripts/build_public_release_20261015.py \
  verify artifacts/public_release_20261015
```

変更していないpayloadの収録一覧・hashを確認し、保存済みの適格性記録4,640件すべてを
二つの計算実装で再計算する。モデルforwardやGPU logitの独立した再構築は行わない。
人の個別回答や過去の因果実験の全状態配列も再計算できない。`publication_verified: false`は
意図した値であり、資料の整合性・保存得点の計算と、[DOIの公開記録](https://doi.org/10.5281/zenodo.23376699)
を区別する。後日の公開に合わせて、パッケージの準備時点のmetadataを書き換えない。
[公開ZIP](../output/artifacts/glyphprobe_public_release_20261015_v2.zip)のSHA-256は
`36959018915a13b988d83b7db13b9e3bb91b6e3a660649cbc8a270340b68f409`。

## 10月15日の独立版の検証記録

独立版PDFは**36ページ**。10月15日の記録では**対象231テストが成功**し、コンパイル時の
はみ出しと未定義参照は0。過去の検査結果であり、10月26日の統合作業でこのsuiteを実行した
という意味ではない。変更していない
[公開文書検証記録](../artifacts/public_release_20261015/evidence/document_validation.public.json)が検査を
PDFのSHA-256 `9f9a34b578b8eeec6dd8f08994fa348ea050d5477c3387663cc885d9cd30d673`に結び付ける。
手元の文書とテストの検証であり、外部公開、科学的な適格性検査の合格、独立した意味の検証を
示すものではない。

## 過去の検証記録

この節の検査とハッシュは、保存した以前のPDFと資料一式に属する。新しい独立版PDFの検査や
公開を示すものではない。今回の梱包・検証の方法は
[PUBLIC_RELEASE_20261015.ja.md](PUBLIC_RELEASE_20261015.ja.md)を参照。

10月15日の旧候補版は35ページ、本文は11ページで終了。補遺Iは29--32ページで、表15--16を追加した。
**対象198テストが成功**し、失敗・エラー・skipは0。コンパイル時のはみ出しと未解決の参照・引用は0で、
余白に関するunderfull警告は残る。全ページを一覧で確認し、改訂本文、入力例、full-state reference swapの表、
追加の結果表は拡大して点検した。最後の組版調整で変わったのは31・34ページだけで、両方を再点検し、
他の33ページの描画画像はbyte単位で同一だった。旧候補版の手元の文書検証記録
（`validation/revised_preprint_20261015/document_validation_v2.json`、今回は未収録）は、
文書の検査、科学的な適格性検査の不合格、外部公開を区別する。PDFのSHA-256：
`8f9f5cc873470b9fcbfed6649adda3a0cfb7cba4dc0c3d7f9cdfcd9c744ce43e`。
版ごとの手元の資料一式（`glyphprobe_revised_preprint_20261015_candidate_v2.zip`、今回は未収録）は、
下記の過去のarchiveとは別物である。収録manifestと再計算方法は[公開候補の案内](RELEASE_CANDIDATE_20261015.ja.md)を参照。
最初の189テストの記録も保存した。最終検査ではmacOSの一時フォルダに関する
パッケージの回帰テスト9件を追加し、科学的入力・得点・PDFは変更していない。
v2アーカイブを別の一時フォルダに展開し、展開したファイルとPython標準ライブラリだけで
検証した。モデルforwardなしで、保存済み得点に対する2実装の検算が一致した。アーカイブのSHA-256：
`8048e9178479d3109e77fb082ab8dda8956b0fcf489644f307da139813fd94ee`。
この候補は過去の手元の成果物として保存し、今回の公開版には別の独立版PDFを用いる。
適格性検査の不合格はどちらの版にも保持する。

保存した10月10日版の検査：29ページ、本文は11ページで終了。補遺Hは24--26ページにある。
追加した4表には、実行形状を揃えた結果、著者回答の分母、モデルの候補選択、質問反転による
対比を記した。関連する65件の検査が通過し、失敗・エラー・スキップはゼロ。
コンパイルにoverfull boxと未定義の参照・引用はなく、余白に関するunderfull警告は残る。
全ページの配置を目視し、変更した本文と表は拡大して確認した。
手元の文書検証記録（`validation/contextual_emoji_working_revision_20261010/document_validation.json`、今回は未収録）で、
文書品質と意味の検証・公開準備を区別する。PDFのSHA-256：
`7ade305ceaea7eaffb9a67b8cce8f301f425e95163e98344a758a834f8879abd`。

保存した10月7日の改訂は、内容が伝わる四つの実験名、共通の入力・読み出し例、トークン数一致の意味、
0.02とblock番号の由来・限界、保存済み集計からの閾値・深度感度を追加した。
応答への効果が実証済みと読める文章も修正した。過去の数値と判定は変更していない。
以下でv3/v4/v5の添付資料の検査を説明する部分は9月の投稿に関する記録であり、
今回匿名packageを再生成したという意味ではない。

保存した10月7日PDFの検査：25ページ、本文は10ページで終了。コンパイルでoverfull boxや未定義の
参照は出ていない。全ページを目視し、最後の改ページ変更後は参考文献・補遺の本文領域が
検収済み画像とpixel単位で一致することを確認した。変化した本文ページは再度目視した。
既存の図・証拠の検査21件も通過。PDFのSHA-256は
`43a5931dd5d3de578818298c8a92fbc9f9244c08d0a821d30fce63e1f4645898`。
新実験のモデル計算より前に行った文書品質の検査であり、科学的成功を示すものではない。
当時は外部への新たな公開を行っていなかった。

論文の文章では、事前指定したプロトコル、評価集合、実行記録など、読者に伝わる語を使う。
技術的なファイル名、登録済みプロトコル、科学的な検証記録の識別子とハッシュは保持する。
箱付きの図は文字と枠の間に最低3ポイントの余白を設け、
`tests/test_paper_figure_layout.py`で72・100・220 dpiの3条件を検査する。
最終PDFも目視で確認する。文字を小さくせずに読みやすさを確保するための検査である。
区間プロットでは、記録済みの区間が軸の範囲からはみ出すと出力を停止する。
Figure 2はMistralのmatched上限0.3531を含む全18区間から表示範囲を決める。

Table 6では7つの副次サイトを明記する。9サイト全て評価済みであり、事前指定した
2つの主要サイトだけに主判定を付ける。この表記変更で検定を追加したり数値を
変更したりしない。

## 過去の事前指定した主張の境界

この節は9月の実験と資料の各版を記録する。文脈実験の開発と読み出し適格性検査については、
[CURRENT_CLAIMS_20261015.ja.md](CURRENT_CLAIMS_20261015.ja.md)で主張の範囲を分ける。

T19の設計は条件付きで連結した二つの結果を報告する。raw atomic emojiは、事前指定した
9つすべてのmodel/tokenizer構成で、literal codepoint stringより語彙的に非重複なCLDR
keyword aliasをよくretrieveした。これは4 viewのtoken countを完全一致させた
解析でも成立した。一方、一つのLlama 3.2 3B構成で事前登録したrank-8の後期
component testでは、T19-Lからhold outした評価emoji 192件に対し、jointに必要かつ
十分なprimary `attn_out` / `mlp_out` siteは見つからなかった。表層はT19以前の
研究に現れた可能性がある。

これはtext-only Unicode入力における限定的な語彙対応を支持する。rendered
glyph知覚、人間的な同義語理解、token identity matching、tokenizer非依存性、
pretraining novelty、普遍manifold、完全な回路、scale lawは示さない。許可・除外
する記述は[CLAIM_TABLE.ja.md](CLAIM_TABLE.ja.md)に記録した。

別途設計を指定したT20-Cでは、追加のemoji 384件と4文脈で最適化rank-8部分空間を調べた。
全状態交換による対照を用いた登録済み判定は、両主要サイトで較正不能となった。
深さ依存の非対称性は回復経路の仮説を動機づけるが、経路の同定や全部分空間の排除は
示さない。

改訂v5でも、別途事前指定した195項目のT21-Cを維持する。コードポイント表記の読み出し
状態への置換後、glyph位置からの情報は、同数の接尾位置対照を上回って対応語の
コサイン・マージンに寄与した。片側・同時95%下限は五つすべて正で、glyph情報の絶対的な
低下・回復による平均top-1効果は0だった。384項目の探索と195項目の確認は分け、
過去のT19/T20の数値・判定・閾値・入力ハッシュは維持する。
[結果の英日レポート](../docs/T21_GLYPH_CONTEXT_PATH_RESULTS_V0.ja.md)を参照。

匿名資料v3には、T19の主要区間の全36検定・記述的区間をモデルなしで再計算する予測index、
T20の採用チェックポイント検証、T21の自項目・競合マージンの事後分解を追加する。
分解は記述的で、確認判定を変更しない。元の195項目の比較値と同時推論の再計算も保つ。
T19 matched emoji数は31–51（Gemma: 51）へ訂正した。元の計算は正しかった。
[査読後の証拠レポート](../docs/POST_REVIEW_EVIDENCE_RESULTS_V0.ja.md)を参照。
生のモデル状態の検証とは区別する。資料v1・v2・v3は過去の手元のarchiveの版であり、
今回の統合では追加しない。archive検証器は全4版を受け付け、変更していないv4を公開payloadに収録する。

資料v4には、読者への伝わり方を整えた最終改稿を含める。要旨は語彙関係の問いから始め、
導入では事前指定したU+1F923 / `lmao`を設計の具体例にする。単語の非重複は公式名と
keywordの間の規則で、部分語や学習時の共起までは排除しない。T20の交換非対称性はT21を
動機づけるが、異なる集団・指標をまたぐ完全な説明や冗長な符号化の証明にはしない。
最終blockの全状態交換は期待される整合性確認、block 24 attentionの`2%`は
sufficiency効果と明記する。

保存済みT21条件別平均から、置換後の基準正答率`3.08%`（pipe）と`0.51%`（article）を
示す。block 21・距離8・全195項目の値である。低さは感度上の留意点であり、床効果の証明や
同等性の主張には使わない。OLMo 2の引用と、Llama mirrorを使う経緯がApple Siliconでの
初期開発にあることも明確にした。この改訂ではモデル実行・統計の再計算を追加せず、実験結果も
変えない。読み取り専用の回帰テストで、記載した百分率を既存の条件別平均に照合する。

補遺G末尾の開示には、著者から申告されたChatGPT・Claude Chatの構成名を投稿前の助言、
Codex・Claude Codeの構成名を実装・解析の役割として記載した。プロトコル設計と編集への
関与も残し、会議の公式査読とは明確に分ける。Checklistの項目16から参照し、匿名提出版に
謝辞の節は含めない。[日英の倫理・開示文書](ETHICS_REVIEW.ja.md)を参照。

改訂v5の最終ローカル検査では、PDFは全23ページ、本文は9ページ目で終わり、参考文献は
10ページ目から始まる。全ページを画像化して確認し、ラベルの欠け、枠からのはみ出し、
未解決の引用は見つからなかった。原稿・図の配置・表に関する選択した回帰テストは
29件すべて通過した。これらは文書と梱包の検査であり、新たな科学実験やOpenReviewへの
投稿完了を意味しない。

原稿では、`T19-L`を語彙観察arm、`T19-C`を条件付きcomponent因果armとして初出時に
定義した。Appendix Aには、初期steering screenからT21-Cまでの探索→確認の短い経路を
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

### Figure 6 (Appendix C) - emojiとsymbolの語彙境界

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

### Figure 3 - 最適化部分空間と全状態交換の対照

- **問い:** T20-Cの9サイトで、最適化rank-8部分空間の効果と状態全体の交換効果は
  どう異なるか。
- **Takeaway:** 主要サイトは登録済み較正基準を満たさず、全状態交換はblock 21/24で
  非対称な効果を示し、block 27では期待されるendpoint整合性確認としてベースライン差を再現する。
- **Family / sufficiency:** 全9サイトの横向き区間プロット。評価emojiは384件、
  各項目4文脈である。
- **Renderer / encoding:** necessityは丸、sufficiencyは四角、全状態交換は白抜き三角。
  主要行を網掛けし、破線は0.02、一点鎖線はベースライン差0.0332を示す。
  点線の0.06はsufficiencyの較正だけに適用する。
- **Output / QA:** `figures/t20_causal_ceilings.pdf`。記録済み推定値と区間を保持し、
  random補正した部分空間効果と未補正の交換効果を区別する。PDFの凡例と縦基準線を確認する。

### Figure 4 - 条件付きglyph位置メッセージの検証

- **問い:** T21-Cでは何を置換し、指定した5つのコサイン・マージン対比はどの程度か。
- **Takeaway:** block 21の読み出し状態を置換した後、glyph位置の情報を崩す・戻す操作は、
  195項目で同数の接尾位置対照を上回る。条件付きマージン効果であり、絶対的な
  top-1の平均効果は0である。
- **Family / sufficiency:** 3段階の模式図と5つの片側区間。元の5対比をすべて表示する。
- **Renderer / encoding:** static Matplotlib。低下は丸、回復は四角、較正は中立色の菱形。
  線分は同時片側95%下限から平均までで、両側信頼区間ではない。
  2つのcarrierと2つのdonorを項目内で平均する。
- **Output / QA:** `figures/t21_path_summary.pdf`。元の`confirmation_result.json`
  だけを入力とし、5下限・ゼロ基準・3解像度での3-pointの箱内余白を確認する。
  本文9ページを保つため、副次的なsymbol比較図をAppendix Cへ移す。

### Figure 5 - 探索から確認へ至る系譜

- **問い:** T19のdesignへ至るまでに、どの先行結果が次の判断を変えたか。
- **Takeaway:** token構造と持続性の研究がendpointを絞り、後続の語彙・因果研究が
  二つのarmを持つdesignを導いた。先行stageはT19-L primaryの証拠分母に入らない。
- **Family / sufficiency:** annotation付きdecision lineage。T1--T20を五つのstageへ
  まとめ、系列を証拠の累積として扱わない。
- **Renderer / encoding:** static Matplotlib。token・持続性diagnosticはgray、
  語彙・boundary研究はblue、T19/T20の検定はorangeで表す。
- **Output / QA:** `figures/t19_lineage.pdf`。全study labelをAppendix Aへ照合し、
  compile済みpaperでbox labelとarrowを検査する。

### Figure 7 (Appendix D) - component-level causal test

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

## 過去のsubmission境界

以下は9月の投稿時の回答と手順を記録したもので、現在の独立版の公開要件ではない。
現在の原稿にはworkshopのチェックリストを含めない。今回の公開状態と範囲は上記に記した。

- 再現に必要な情報の開示は`Yes`。プロトコル、モデルの正確なrevision、項目選択、
  訓練設定、seed、解析コードを示し、参照先checkpointから再取得できる。
- open accessとcomputeは`No`のまま。compact artifactはraw arrayと完全な介入記録を
  含まず、T19の正確な取得時間・peak memoryも提出記録に含まれない。
- double-blind copyの凍結後にだけauthor listとacknowledgmentsを確定する。
- OpenReview recordを検証できるだけ早くuploadする。

過去の原稿のData/codeのopen accessへの回答は、**N/AではなくNo**だった。公式checklistで
N/Aが許されるのは、codeを要する実験を含まないpaperである。査読後の公開予定だけでは
submission時点の回答は変わらない。新archiveは匿名compact auditとdocumentation gapを
閉じたが、exact raw replayまでは閉じていない。License、ethics、new-asset documentation、
保守的なLLM-assistance declarationは完了した。
