# GlyphProbe 研究ロードマップ

[English](ROADMAP.md) · [E2 MLX validationプロトコル](LLAMA32_3B_MLX_VALIDATION_PROTOCOL.ja.md) · [E1 探索結果](EMOJI_FAMILY_EXPLORATORY_RESULTS.ja.md) · [E1 探索プロトコル](EMOJI_FAMILY_EXPLORATORY_PROTOCOL.ja.md) · [Milestone 2 結果](MILESTONE2_RESULTS.ja.md) · [基準実験の結果](RESULTS_V1.ja.md) · [Phase I 論文計画](PAPER_OUTLINE.ja.md)

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

状態: 運用上は完了。結果はレイヤーごとに分かれ、論文での最終的な推論上の位置づけは未確定。

- 公開凍結と事前検査の合格後、48件のP2バンクを一度だけ開いた。別に凍結した48件のC1因果ホールドアウトは未使用のまま残した。
- 色付き図形パネルを、指定済みのGPT-2トークン数と、パネル単位の9対1の接頭構造を揃えた、互いに重ならない10記号のnull対照パネル3組と比較した。
- token IDを完全に一致させる対照は主張の範囲外とする。同じtoken ID列は同じ入力byte列へ復号されるため、ここで行うのはトークン化の影響を除去したglyph試験ではなく、指定済み対照に対する頑健性試験である。
- 主要仮説はlayer 2とlayer 4、strength 0.05に固定し、direction seedは各target内で平均した。
- 凍結済みv1では、layer 2が両方のsource-wrapper条件で指定済みmatched controlsに対して頑健と判定された。主要ソースは+0.208363、95% CI [0.137463, 0.276893]、Holm p = 0.00143999。独立ソースは+0.187507、[0.125489, 0.247659]、p = 0.00393996だった。
- Layer 4は両条件とも未解決だった。主要ソースは-0.0329465、[-0.0761085, 0.0110094]。独立ソースは-0.086379、[-0.159246, -0.016917]である。
- 元の探索行列では、96次元のpaired median excessが記述的に+0.047427、正セルは25 / 36だった。「何%を説明したか」という推定には使わない。
- 公開した全14 run、すなわち探索・P2・独立ソースの中核12 armと診断2 runについて、別のrole/input-binding auditが合格した。
- v1のbootstrap区間は固定済みtarget効果を再標本化し、各replicateでprototypeを作り直さない。Prototypeを共同で再構築する事後感度分析では区間が広がったが、p値やstatusは付与せず、v1判定も上書きしない。
- 2つの二次診断はいずれも14,208行のgridを完走し、errorは0件、zero-hook RMSは0、readinessは11 / 11だった。Random-adjustedのheadline優位量は、末尾token一致で+0.751225、接頭構造均一化で+0.601038だった。これはpaired comparisonのraw separation scoreとは別の評価量である。
- 96 / 48 / 32 / 24次元における記述的なstandard-minus-suffix raw-separation中央値は、+0.002624 / +0.009473 / +0.004026 / +0.009700。Standard-minus-prefixは、+0.022096 / +0.023254 / +0.011040 / +0.025387だった。96次元で正だったのは、それぞれ20 / 36セルと25 / 36セルである。この事後診断は推論も同等性判定も与えず、低次元値は同じseedによる代数的な畳み込みである。
- Matched-null Aの最初のprocessは、マシン負荷が極端に高い最中、798行で外部から中断された。Sealを保ったresumeによって、重複・欠損・error・非ゼロのzero-hook RMSなしで正確なgridを完了した。これは実行時の来歴であり、モデルに関する証拠でも、一般化できる速度の主張でもない。

凍結済みの問いと判定規則は [Milestone 2 プロトコル](MILESTONE2_PROTOCOL.ja.md)、結果と留保は [Milestone 2 結果](MILESTONE2_RESULTS.ja.md) に記録した。

終了条件: 運用上の実行は完了した。論文での最終的な確認表現と、それを支える再現実験では、run roleを凍結済みinputへ事前に直接結び付け、データ依存prototypeの再標本化を扱う。

### 探索side track E1 — トークン同型な絵文字familyのスクリーニング

状態: 範囲を限定した記述的探索として完了。公開commit
`0cd4e11610e42253ead9ce9aff9f0b02474a0558`で実行条件を凍結した後、
5本のMLX runを実施した。

- 10 code pointからなる5 blockを固定する。`sky`（`U+1F311`–`U+1F31A`）、`food`（`U+1F351`–`U+1F35A`）、`animals`（`U+1F411`–`U+1F41A`）、`transport`（`U+1F691`–`U+1F69A`）、`social`（`U+1F911`–`U+1F91A`）である。
- 各glyphを固定GPT-2で3 tokenとし、family間では第1 tokenと対応slotの第3 tokenを一致させ、第2 tokenだけをfamilyごとに変える。
- 既存`prestage_targets`の先頭24件と16件のsource wrapperだけを再利用する。P2とC1は、読み込み、tokenize、score、選択のいずれにも使わない。
- Run familyは、固定GPT-2、MLX FP32、`resid_post`のlayer 2・4、strength 0.05、seed 101 / 211 / 307、各layerのrandom direction 2本に限定する。Zero-hook checkは有効、neutral-direction armとsign-flip armは無効とする。
- Layer 2をprimary exploratory rowとした。事前指定したlayer 4のnegative comparatorは、結果としてnegativeにならなかった。
- ReplicateごとにLOTO prototypeを作り直し、\(M_{f\leftarrow g}\)行列全体、within-row超過量\(R_f\)、family等重みの\(R_{\mathrm{global}}\)を報告する。Primary descriptive aggregateはtarget等重みの平均とし、データ依存prototypeは、target groupで層化した20,000回のbootstrap内でも毎回再構築する。
- 5本のrunは全8,880介入行を完走した。Errorは0件で、zero-hookのactivation/logit RMSは正確に0だった。
- Family等重みのglobal超過量は、layer 2で0.014752595564、95%記述区間[0.002875238085, 0.027439243404]、layer 4で0.014887989201、[0.003407563347, 0.019684351979]だった。
- Family別区間は、両layerの5 familyすべてで0を含んだ。
- 平均transfer行列は広く正だった。25 cellの範囲はlayer 2で0.395455〜0.484915、layer 4で0.602564〜0.681909だった。
- Family × layer × seedの30 cell中10 cellはrandom controlを上回らなかった。Layer 2のseed 307とlayer 4のseed 101で、それぞれ5 familyすべてが該当した。
- 凍結後は全familyを公開し、null、負、不均一なcellも残す。P値、多重性判定、確認的status labelは付けない。

[E1 探索プロトコル](EMOJI_FAMILY_EXPLORATORY_PROTOCOL.ja.md)では、問い、input、endpoint、停止規則、主張境界を定め、[E1 探索結果](EMOJI_FAMILY_EXPLORATORY_RESULTS.ja.md)では全結果を公開した。広く正のtransfer行列と小さなfamily固有超過は、共有tokenによるtransferが残差的なwithin-family信号より支配的であることを示唆する。E1で記述できるのは、統制した中間token置換の下でのmatched-slot反復までである。意味上のfamily効果、tokenization非依存の性質、layer固有の効果、random controlに対する頑健な優位性、因果mechanism、modelをまたぐ規則性は主張しない。Milestone 2の判定を更新せず、C1を開かず、Milestone 3の介入も選ばず、Phase I論文gateも満たさない。

終了条件: 達成。公開bundleは、tokenizer-only preflight、全記述解析、5つの軽量run directory、root manifestを結び付けている。E1から新しい仮説を立てる場合は、P2でもC1でもない未使用target bankを用意し、新しい確認プロトコルを先に公開する。

### Engineering side track E2 — Llama 3.2 3B MLX cross-model transport

公開freeze commitでの状態: engineering protocol frozen / validation pending。
Commit公開前の実効statusは`freeze_pending`のままとする。どちらの状態でも、E2の
科学的model forwardも結果も認めない。

- まず、base modelである`mlx-community/Llama-3.2-3B-bf16`のrevision
  `60a99aaf43164077157d64bf909b7b61143c6a6d`について、process-isolatedな
  Transformers/MPS-to-MLX parityとlocal speedのvalidationを凍結し、実行する。
- Native BF16、`add_special_tokens: false`、`last_nonpad`の`resid_post`、
  layer 5・11を用いる。Layerは、期待されるdecoder 28層に対して、固定した相対
  depth 0.2・0.4から導出する。
- MLXを今後のE2 cellへ選択する前に、固定済みのnumerical parity、zero-vector、
  intervention fidelity、token ID、argmax、speedの全checkへ合格することを求める。
- Stage Aのinputは、E1 endpoint/gridとすべてのtarget/source-wrapper bankの外に
  置いた固定engineering probeに限る。Surface coverageのため、そのうち3件では
  公開済みE1 panelのglyphを使うが、科学的outcome inputには用いない。P2とC1は、
  読み込み、hash、tokenize、forward、解析のいずれも行わない。
- ImmutableなStage-A receiptが合格した場合に限り、科学的outcomeを見る前に、
  E2のtokenizer audit、run config、解析、manifestを公開freezeする。
- E1の元の50絵文字すべてをprimary literal setとして保ち、5 familyのslot
  03--09を、固定した35 glyphのtoken-structural sensitivityとして事前指定する。
- すでに探索に使った同じ24件のprestage targetと、同じ16件のsource wrapper
  だけを再利用する。Confirmatoryとは表現しない。
- その後E2 gridを実行しても、範囲を限定したtransport observationとして報告
  する。Model、tokenizer、vocabulary、architecture、dtypeがすべて同時に変わる
  ため、model scaleの効果だけを識別できず、scale effectを確立できない。

固定するengineering gateは、[E2 Stage-A MLX validationプロトコル](LLAMA32_3B_MLX_VALIDATION_PROTOCOL.ja.md)
に記載する。このgateへの合格と別の科学的freezeの公開が完了するまで、E2は
cross-model replicationでもmodel-generalな絵文字効果の証拠でもなく、Phase I
論文gate 5も満たさない。

終了条件: 固定model/configuration identityを、完全なbackend parityおよび
Transformers/MPSの95%以下となるmachine-localなMLX aggregate median latencyへ
結び付けたatomic・no-overwrite receiptを1件作る。この終了条件が認定するのは
engineering routeだけであり、E2や論文gateは完了しない。

### Milestone 3 — 対象を絞った因果局在化

状態: プロトコル設計へ進める。ただし、因果プロトコルはまだ凍結しておらず、因果主張も認めない。現時点の候補はlayer 2だけで、layer 4は未解決のため候補にしない。別の確認用bankは、このプロトコル設計に着手するための前提条件ではない。

- モデル系列ごとのparity確認後に限り、`resid_pre`、`attn_out`、`mlp_out`、`resid_post`を比較する。
- 事前指定した候補レイヤー周辺で、component patchingとpath patchingを行う。
- ablation、restoration、projection-removal介入を用いる。
- 候補fingerprintを変えないはずのnegative controlを含める。
- 一度の大きなdriftではなく、holdout上での選択的効果を要求する。
- 介入、endpoint、対照、候補layer、多重性familyを新しい公開因果プロトコルに凍結するまで、C1は開かない。

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

状態: Milestone 2 v1について一部完了。ただし、bootstrap依存の扱いは未確定。

- target promptを主要な標本clusterとして扱う。
- direction seedとtarget splitは入れ子の反復とし、独立標本として数えない。
- primary endpointと、小さく限定したprimary hypothesis familyを定義する。
- そのfamilyに適した多重性補正を用いる。
- p値と併せて、効果量、区間、負のセル、感度分析を報告する。
- `1/1001`の置換下限と、全体有意性の主張を区別する。
- 次の確認analyzerでは、CLI順序と別監査に頼らず、科学的なrun roleを凍結済みconfigとinputへ直接結び付ける。
- データから推定するprototypeは各再標本内で作り直すか、別の依存対応estimatorを結果確認前に根拠とともに凍結する。

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

現時点では、ゲート1〜3に実行上の根拠がある。ただし、prototype再構築解析が事後的だったため、ゲート6の最終的な統計資格は未確定である。ゲート4、5、8、10は未完了。ゲート9は、公開文書を更新するたびに維持する。英語論文がPhase Iの終点であり、現在のリポジトリはエビデンスを伴う研究リリースであって、完成原稿ではない。

## Phase I より先の候補

Phase IIでは、E1で固定した5つの絵文字blockを超える拡張、multimodal tokenizer、学習済みfeature basisの解析、intervention orbit、training checkpoint間の比較などが候補になる。Phase I論文が完了するまでは、現在の実施範囲に含めない。
