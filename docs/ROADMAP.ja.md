# GlyphProbe 研究ロードマップ

[English](ROADMAP.md) · [現在の結果](RESULTS_V1.ja.md) · [Milestone 2 プロトコル](MILESTONE2_PROTOCOL.ja.md) · [Phase I 論文計画](PAPER_OUTLINE.ja.md)

## 到達点

Phase I の到達点は、英語プレプリントとして公開できる論文と、監査可能な証拠一式です。現在固定しているGPT-2 MLX runは、そのための基準地図であり、最終的な主張ではありません。

Phase Iを通して、リポジトリで作成する公開文書は英語版と日本語版を対にして管理します。論文は英語版を正文とし、日本語の併記文書によって、研究過程を読みやすく、検証しやすい状態に保ちます。

## 研究の順序

### Milestone 1 — 再現可能なスクリーニング基準

状態: 固定済みのGPT-2 FP32 `resid_post`セル1件について完了。

- パネル、ラッパー、ターゲット、強度、レイヤー、対照を固定する。
- 対象モデルセルに限って、MLXをTransformers/MPSと照合する。
- 14,208レコードの標準行列を実行する。
- 行数、来歴、ゼロ介入、スカラー量の均衡、主要集約値の再計算を監査する。
- 正のセル、負のセル、不均一なセルをまとめて公開する。

終了条件: 内部整合性のある前因果的候補が得られていること。この段階では、意味や因果を示す表現は認めない。

### Milestone 2 — トークン化対照とnull対照の強化

状態: プロトコル凍結済み、事前検査待ち。Milestone 2のモデル出力は、まだ確認も主張もしていない。

- 凍結済みのP2バンク（48件）を確認実験で一度だけ使い、別に凍結したC1バンク（48件）は将来の最終因果試験まで残す。
- 色付き図形パネルを、指定済みのGPT-2トークン数と9対1のトークン接頭構造を揃えた、互いに重複しない10記号のnull対照パネル3組と比較する。
- token IDを完全に一致させる対照は主張の範囲外とする。同じtoken ID列は同じ入力byte列へ復号されるため、ここで行うのはトークン化の影響を除去したglyph試験ではなく、指定済み対照に対する頑健性試験である。
- 主要仮説をlayer 2とlayer 4、strength 0.05に固定し、direction seedは各target内の反復推定として扱う。
- 48件のターゲットプロンプトを標本クラスタとし、leave-one-group-out prototype、group内で再標本化するtarget-cluster bootstrap区間、2つのprimary layerに対するHolm補正で主要効果を推定する。
- 実装確認と診断には既存24 targetを使い、debugや調整にholdout bankを使わない。
- P2バンクを一度だけ開く前に、manifest、config、解析コード、testの事前検査を完了する。

問い、endpoint、判定規則、停止規則、禁止事項の詳細は [Milestone 2 確認実験プロトコル](MILESTONE2_PROTOCOL.ja.md) に固定しています。このプロトコルと、対応するmanifest、config、解析コードを初めて含む公開コミットを凍結時点とします。公開凍結が成立し、すべての事前検査を通過するまで、P2バンクは開きません。

終了条件: 確認実験の効果が、現在判明しているトークン長またはトークン接頭構造の非対称性だけでは説明できないこと。

### Milestone 3 — 対象を絞った因果局在化

状態: 計画中。

- モデル系列ごとのparity確認後に限り、`resid_pre`、`attn_out`、`mlp_out`、`resid_post`を比較する。
- 事前指定した候補レイヤー周辺で、component patchingとpath patchingを行う。
- ablation、restoration、projection-removal介入を用いる。
- 候補fingerprintを変えないはずのnegative controlを含める。
- 一度の大きなdriftではなく、holdout上での選択的効果を要求する。

終了条件: 事前指定した介入が候補効果を選択的に変え、matched controlsを通過すること。それまでは`causal_claim_authorized`を`false`のまま保つ。

### Milestone 4 — 再現と適用境界の把握

状態: 計画中。

- adapter-level parityだけでなく、raw TransformersまたはTransformerLensで確認セルを再実行する。
- 少なくとも1つの別model familyとtokenizerで再現を試みる。
- weight履歴を利用できる場合は、checkpoint間での出現時期を調べる。
- prompt domainとtarget template familyをまたいで頑健性を検証する。
- architecture固有の観測と、modelをまたぐ規則性を分ける。

終了条件: 何が再現し、何がGPT-2固有のままかを論文で明確に述べられること。

### Milestone 5 — 確認的統計

状態: 計画中。

- target promptを主要な標本clusterとして扱う。
- direction seedとtarget splitは入れ子の反復とし、独立標本として数えない。
- primary endpointと、小さく限定したprimary hypothesis familyを定義する。
- そのfamilyに適した多重性補正を用いる。
- p値と併せて、効果量、区間、負のセル、感度分析を報告する。
- `1/1001`の置換下限と、全体有意性の主張を区別する。

終了条件: 標本構造に合った統計解析を、凍結済みartifactから再実行できること。

### Milestone 6 — 英語論文とアーカイブ公開

状態: Phase Iの目標。

- 文章を磨く前に、英語論文の主張表を凍結する。
- 主要な図表を、バージョン管理した解析scriptから直接生成する。
- model、revision、tokenizer、environment、implementation、inputのreceiptを公開する。
- 完全なraw ledgerと必要なarrayを保管する。難しい場合は、統制された再現可能なアクセス方法を文書化する。
- checksumと省略記録を明記した、コンパクトなrepository packageを公開する。
- 内部の反証レビューと、独立した再現試行を完了する。
- 英語プレプリントと日本語の公開概要を発表する。

終了条件: 論文の各主張が凍結済みartifactを参照し、重要な留保がabstractまたはLimitationsに現れ、独立した読者が欠けた証拠を推測で補わずに解析を再現できること。

## Phase I 論文のゲート

次の条件をすべて満たすまで、論文をdraftからpreprintへ進めません。

1. primary hypothesisと主張境界を正確に凍結する。
2. 確認用target setを探索的な選択に触れさせない。
3. トークン化を揃えた対照実験を完了する。
4. 正負を問わず、対象を絞った因果実験を少なくとも1件完了する。
5. 独立したbackendまたはmodelでの再現を少なくとも1件完了する。
6. cluster構造と多重性を反映した統計を報告する。
7. 負のセルと不均一なセルを、本文または補足で見える状態に保つ。
8. 完全な証拠archiveを保管し、checksumを付ける。
9. リポジトリの英語・日本語文書を同期する。
10. 英語論文について、先入観のない再現性・主張境界レビューを行う。

これらのゲートは、正の結果を前提にしていません。実験の識別可能性とartifactの完全性を保てるなら、境界を明確にした負の結果やmixed resultも、Phase Iの妥当な到達点です。

## Phase I より先の候補

Phase IIでは、より広いsymbol family、multimodal tokenizer、学習済みfeature basisの解析、intervention orbit、training checkpoint間の比較などが候補になります。Phase I論文が完了するまでは、現在の実施範囲に含めません。
