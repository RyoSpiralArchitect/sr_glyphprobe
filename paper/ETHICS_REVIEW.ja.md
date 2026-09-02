# Ethics・responsible-release review

[English](ETHICS_REVIEW.md)

状態: [NeurIPS Code of Ethics](https://neurips.cc/public/EthicsGuidelines)に
照らした**著者側reviewを2026-09-02に完了**。これは本scopeに限ったself-auditであり、
institutionalな法的判断やIRB判断ではない。

## Scope review

| 領域 | T19/T20/T21の確認結果 | 緩和策・境界 |
|---|---|---|
| Human participant・crowdsourcing | なし | 募集、指示、報酬、介入、IRB対象となるparticipant procedureは存在しない。 |
| Privacy・personal data | なし | 入力は公開Unicode scalar、標準化された英語annotation、literal codepoint string、固定carrier tokenだけ。user message、account、identifier、個人contentのscrapingはない。 |
| Data・model terms | 確認済み | Model weightはupstream termsに従って取得し、再配布しない。Qwen2.5 3Bは非商用研究だけで使用。Unicode派生行にはUnicode License v3 noticeを同梱する。`ASSET_LICENSES.md`参照。 |
| Representativeness | 重要な限界あり | CLDR英語annotationはstandards metadataであり、普遍的人間意味、familiarity rating、population sampleではない。paperは文化・感情・identityへの一般化を禁止する。 |
| Scientific integrity | 統制済み | 事前指定したendpoint/item bank、負の結果、過去の確認失敗、多重性rule、effect-size floor、raw-data欠落を保持する。T21-Cの新しいマージン指標と肯定結果は、変更していないT19/T20のtop-1判定と分ける。archiveはhash integrityを科学的正しさへ格上げしない。 |
| Misuse | capability riskは低いが解釈riskはゼロでない | 新modelや運用可能なsteering capabilityは公開しない。主なriskは語彙対応から不当なprofiling・文化推論を行うことであり、paperはその使用を明示的に除外する。 |
| Environmental impact | 有限の実験、正確なimpactは不明 | モデル重みは訓練していない。T20-Cでは小さな部分空間パラメータを最適化した。forward数とT20/T21の所要時間は報告し、未記録のT19所要時間・最大メモリ・energy・carbonは事後推定しない。 |

## LLM assistanceの開示

LLM coding/research assistantは段階的なprotocolの開発、code生成、解析、manuscript編集、
著者側のfresh-eyes reviewを支援した。T21の問いはT20と明示した使用済み項目での探索を
受けて作り、残る195項目へアクセスする前に確認実験の指標と規則を記録した。ラベルは
CLDRから取得し、assistantの判断を実験測定値には使っていない。実行権限と最終主張への
責任は著者が保持する。数値出力と別実装のvalidatorはchecksumで対応づけた。
これは外部の再現実験や著者の検討を代替するものではない。

assistant output自体は実験measurementではないが、研究workflowには影響したため、保守的に
開示する。

## 結論

宣言scope内でT19/T20/T21は、確認したNeurIPS ethics原則に適合する。licensed public resourceを
使い、人・personal dataを扱わず、不利なevidenceを保持し、主要なrepresentational/misuse
riskを明示した。残るcompute accountingの欠落は`COMPUTE_REPORT.md`に開示しており、
隠した値ではなくtransparency上の限界である。
