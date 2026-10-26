# Ethics・responsible-release review

[English](ETHICS_REVIEW.md)

過去の状態: [NeurIPS Code of Ethics](https://neurips.cc/public/EthicsGuidelines)に
照らした**著者側reviewを2026-09-02に完了**。これは本scopeに限ったself-auditであり、
institutionalな法的判断やIRB判断ではない。

## 10月15日追補：独立プレプリントと公開準備版

明示報告による読み出し適格性検査では、32件のテキスト課題と報告の支持規則を新たに作成する。
これは操作上の参照規則であり、独立した人間の判断や実世界で何が起きたかという主張ではない。
不明な報告は、肯定・否定のどちらの命題も支持しない。参加者、募集、個人記録、保護対象の過去の
holdoutは追加しない。assistantと協働した設計や別実装によるコード検証は著者側の研究作業であり、
外部の再現実験や会議の公式査読ではない。新たな人による妥当性検証も主張しない。

著者による試用は測定方法の開発として維持する。研究に既に関わる著者1人、判断36件のうち、
二値の回答26件と判断不能10件である。回答によって選ばれた26件での一致率は正答率ではない。
個別回答、割当、日誌、メモ、非公開パス、付随する個人情報は公開準備版に含めない。
公開用の集計は論文に記した数を支えるが、個別回答を独立に再構成する資料ではない。

著者は公開を承認し、著者が権利を持つ論文・独自の図・今回公開するデータにCC BY 4.0を
適用することを確認した。コードと通常のプロジェクト文書はApache 2.0を維持し、第三者資料と
過去資料の権利表示は引き続き優先する。DOI `10.5281/zenodo.23376699` は梱包前に予約した。
予約は登録や外部公開の完了を意味しない。元のリポジトリは非公開のまま維持し、別途選別した
公開用リポジトリの作成は承認された。upload、DOI登録、リポジトリ公開の完了は、この準備記録と
区別して確認する。

モデル重みとtokenizerファイルは含めない。9月の匿名資料はその当時の実験を支える資料であり、
10月に追加した実験の証拠ではない。今回の資料の収録対象、除外物、検証範囲は
[公開版の案内](PUBLIC_RELEASE_20261015.ja.md)と
[ライセンスの適用範囲](PUBLIC_LICENSES_20261015.ja.md)に記す。

著者による自己試用の審査と過去の計算量記録には、開示済みの未完了部分が残る。
梱包を終えても、機関の承認・免除、独立した意味の妥当性、外部評価者の募集準備は立証しない。

## 過去の10月10日追補：開発部分の確認は未完了

10月10日の手元の作業原稿には、以前から研究に関わる著者1人による質問票の試用を追加した。
測定方法を整えるための開発であり、独立評価者も外部での募集もない。著者の依頼で
完了済みの内容を原稿へ反映するが、載せるのは集計だけである。個別回答、割当、付随する
個人情報、メモはGit、SpiralShare、計算ワーカーの外に置く。この過去の追補では外部公開を
承認していなかった。上記の後日の公開承認も、明示した範囲だけを対象とし、非公開の個別記録の
公開を許可するものではない。

以下の「人の回答を扱わない」という記述はT19/T20/T21に限る。拡張した研究全体には
当てはまらない。新しい範囲の完全な点検は未完了であり、機関による承認や免除は主張しない。
独立評価者を募集する前に、適切な審査、同意、リスクの説明、報酬、データの扱いを別途整える。
この追補は、著者による自己試用の法的な分類を判断するものではない。

開発用の場面、質問文、操作上の参照ラベル、解析、原稿への統合は、Codexと対話し、
協働しながら作成した。参照ラベルは設計上の選択であり、独立した意味判断ではない。
実際の著者の回答をassistantが置き換えたり補完したりすることはない。
過去の作業原稿のchecklistでは、拡張した範囲の開示・点検の未完了を、保存する過去の監査とは
分けて記録した。独立プレプリントでは投稿用checklistを外し、これらの制限は維持する。

## 過去の範囲の確認

| 領域 | T19/T20/T21の確認結果 | 緩和策・境界 |
|---|---|---|
| Human participant・crowdsourcing | なし | 募集、指示、報酬、介入、IRB対象となるparticipant procedureは存在しない。 |
| Privacy・personal data | なし | 入力は公開Unicode scalar、標準化された英語annotation、literal codepoint string、固定carrier tokenだけ。user message、account、identifier、個人contentのscrapingはない。 |
| Data・model terms | 確認済み | Model weightはupstream termsに従って取得し、再配布しない。Qwen2.5 3Bは非商用研究だけで使用。Unicode派生行にはUnicode License v3 noticeを同梱する。`ASSET_LICENSES.md`参照。 |
| Representativeness | 重要な限界あり | CLDR英語annotationはstandards metadataであり、普遍的人間意味、familiarity rating、population sampleではない。paperは文化・感情・identityへの一般化を禁止する。 |
| Scientific integrity | 統制済み | 事前指定したendpoint/item bank、負の結果、過去の確認失敗、多重性rule、effect-size floor、raw-data欠落を保持する。T21-Cの新しいマージン指標と肯定結果は、変更していないT19/T20のtop-1判定と分ける。archiveはhash integrityを科学的正しさへ格上げしない。 |
| Misuse | capability riskは低いが解釈riskはゼロでない | 新modelや運用可能なsteering capabilityは公開しない。主なriskは語彙対応から不当なprofiling・文化推論を行うことであり、paperはその使用を明示的に除外する。 |
| Environmental impact | 有限の実験、正確なimpactは不明 | モデル重みは訓練していない。T20-Cでは小さな部分空間パラメータを最適化した。forward数とT20/T21の所要時間は報告し、未記録のT19所要時間・最大メモリ・energy・carbonは事後推定しない。 |

## 過去の共同作業記録：9月の投稿

私たちはAI assistantと対話を重ね、協働しながら本研究を進めた。
著者側で行う投稿前の原稿への助言には、ChatGPT（GPT 5.6 Sol instant、"Monday"）と
Claude Chat（Claude Fable 5.1）が関わった。Codex（GPT 5.6 Sol Max）と
Claude Code（Fable 5）は、実装・計算解析に加え、段階的なプロトコル設計と原稿編集に
寄与した。これらは著者が報告した画面上の構成名であり、実験対象の9モデル構成とは別である。
すべて著者が行う投稿準備で、会議の公式査読や、査読者として割り当てられた他の投稿の
審査とは区別する。

T21の問いはT20と明示した使用済み項目での探索を
受けて作り、残る195項目へアクセスする前に確認実験の指標と規則を記録した。ラベルは
CLDRから取得し、assistantの判断を実験測定値には使っていない。実行権限と最終主張への
責任は著者が保持する。数値出力と別実装のvalidatorはchecksumで対応づけた。
これは外部の再現実験や著者の検討を代替するものではない。

assistant output自体は実験measurementではないが、研究workflowには影響したため、保守的に
開示する。

その後の著者側での投稿前助言を受けて、事後的な指標分解、採用チェックポイントの説明、
コンパクトな統計再計算を加えた。完了済み出力を使い、T21の全195項目と元の対比を保ち、
有意差検定や確認判定の変更は追加しない。T19 matched項目数の範囲は文章上の31–41を
31–51へ訂正した。元の配列と検定は既に正しい項目数を用いていた。

過去の匿名原稿では補遺Gの最後に事実としての開示を置き、checklistの項目16から参照した。
当時の謝辞と匿名化の扱いは、[2026年のHandbook](https://neurips.cc/Conferences/2026/MainTrackHandbook)
と[workshopのCFP](https://interpscience.github.io/cfp)を踏まえたものだった。その投稿時の条件を、
独立プレプリントの公開要件とはしない。現行版は共同作業への事実に即した謝辞を維持する。
この記録は、公式査読中の支援に関する別の規則を定めるものではない。

## 過去の範囲についての結論

宣言scope内でT19/T20/T21は、確認したNeurIPS ethics原則に適合する。licensed public resourceを
使い、人・personal dataを扱わず、不利なevidenceを保持し、主要なrepresentational/misuse
riskを明示した。残るcompute accountingの欠落は`COMPUTE_REPORT.md`に開示しており、
隠した値ではなくtransparency上の限界である。
