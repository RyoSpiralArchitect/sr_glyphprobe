# Phase I 英語論文の構成案

[English](PAPER_OUTLINE.md) · [ロードマップ](ROADMAP.ja.md) · [E2 MPS transport v2プロトコル](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.ja.md) · [v1 preflight failure](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.ja.md) · [holdout状態](HOLDOUT_STATUS.ja.md) · [E1 探索結果](EMOJI_FAMILY_EXPLORATORY_RESULTS.ja.md) · [Milestone 2 結果](MILESTONE2_RESULTS.ja.md) · [基準実験の結果](RESULTS_V1.ja.md)

この文書は、日本語で研究設計を確認するための構成案です。Phase I の論文本体は英語で執筆します。

## 仮題

**From Glyph Directions to Output Fingerprints: A Controlled Pre-Causal Study in GPT-2**

因果実験が成立しない場合は、`Pre-Causal` を残します。限定した回路介入まで成立した場合に限り、題名と要旨で因果性を表す語を再検討します。

## 現時点で守れる中心命題

> 固定したGPT-2 FP32 MLX `resid_post`条件では、layer 2の色付き図形fingerprint scoreが、凍結済み48 target bank上で、指定済みのトークン数・接頭構造matched panel 3組を2種類のsource-wrapper構成で上回った。凍結済みv1では両方のlayer 2条件を頑健と判定したが、layer 4は両方とも未解決だった。これは前因果段階のmixed resultであり、トークン化から独立した効果、意味、機構、modelを越えた一般化ではない。

この命題も暫定版である。v1のrole bindingと固定prototype bootstrapに関する留保を、次の結果を見る前に解決してから、論文の最終的な確認命題を凍結する。

## 現在のMilestone 2主張表

| 条件 | レイヤー | 凍結済みv1結果 | 事後prototype再構築感度 | 現時点での論文上の扱い |
|---|---:|---|---|---|
| 主要ソース | 2 | +0.208363、95% CI [0.137463, 0.276893]、Holm p = 0.00143999、頑健 | [0.099930, 0.295380] | 正の候補。事後区間を確認結果へ格上げしない |
| 主要ソース | 4 | -0.0329465、[-0.0761085, 0.0110094]、未解決 | [-0.099995, 0.041902] | 未解決の負・mixed evidence |
| 独立ソース | 2 | +0.187507、[0.125489, 0.247659]、Holm p = 0.00393996、頑健 | [0.104210, 0.271322] | source構成への頑健性。独立target/model再現ではない |
| 独立ソース | 4 | -0.086379、[-0.159246, -0.016917]、未解決 | [-0.185084, 0.007648] | 未解決の負・mixed evidence |

事後解析は、共同target bootstrapの各replicate内で、すべてのleave-one-target-group-out prototypeを作り直す。p値やstatusは付与せず、v1も上書きしない。独立ソースの正確な数値と限界は、公開済み感度分析receiptへ結び付ける。

## 現在の二次診断表

2つの診断runはいずれも14,208行を完走し、errorは0件、zero-hook RMSは0、readinessは11 / 11だった。Random-adjustedのheadline `emoji_fingerprint_advantage`は、末尾token一致が+0.751225、接頭構造均一化が+0.601038だった。このheadline値は、下表のraw separation scoreとは別の評価量である。

| CountSketch次元 | Standard minus suffix raw separationの中央値 | Standard minus prefix-homogeneous raw separationの中央値 |
|---:|---:|---:|
| 96 | +0.002624 | +0.022096 |
| 48 | +0.009473 | +0.023254 |
| 32 | +0.004026 | +0.011040 |
| 24 | +0.009700 | +0.025387 |

96次元で正だったのは、suffixが20 / 36セル、prefixが25 / 36セルである。これは事後的・記述的な診断であり、推論や同等性の解析ではない。低次元値は同じseedによる代数的な畳み込みで、独立した再実行でもseed感度でもない。

## 現在のE1探索side result

E1では、10 glyphからなる5 familyについて、第1・第3 GPT-2 tokenをfamily間で
固定し、中間tokenだけを置換した。Family等重みのglobal specificityは、
layer 2で0.014752595564（95%記述区間
[0.002875238085, 0.027439243404]）、layer 4で0.014887989201
（[0.003407563347, 0.019684351979]）だった。Family別区間は、両layerの
5 familyすべてで0を含んだ。Transfer行列は広く正で、layer 2では
0.395455〜0.484915、layer 4では0.602564〜0.681909だったが、
family × layer × seedの30 cell中10 cellはrandom controlを上回らなかった。

事前指定したlayer 4のnegative comparatorはnegativeにならなかった。
したがって、許される解釈は、固定した中間token置換下で共有tokenに結び付く
matched-slot反復が見られ、family固有の上乗せは小さかった、という範囲に
限られる。意味上のfamily構造、tokenizer非依存性、layer固有性、random
controlに対する頑健な優位性、因果性は主張しない。E1は探索済みtarget
24件を再利用し、P2とC1を使っていない。Milestone 2の判定も論文gateも
更新しない。

## 研究質問

1. **RQ1 — 測定の忠実性:** 要求したRMS介入は実測値と一致し、ゼロ介入は真に無作用か。
2. **RQ2 — 指紋の再現性:** 同じグリフから別々に推定した方向は、未使用ターゲットでも似た出力差分を生むか。
3. **RQ3 — 対照との差:** その再現性は、同じノルムのランダム方向、一般絵文字方向、ラベル置換より高いか。
4. **RQ4 — 条件依存性:** 効果はレイヤー、強度、ソース方向、ターゲット群、指定済みのトークン数・接頭構造matched controlsでどう変わるか。
5. **RQ5 — 因果性:** 候補コンポーネントのアブレーションと復元で、指紋を選択的に消し、戻せるか。
6. **RQ6 — 独立再現:** どの結果が、実行backend、tokenizer、model familyをまたいで再現するか。
7. **RQ7 — 共有token間のtransfer:** トークン同型な探索panelで、matched-slot反復は中間token familyをまたいでどの程度移り、family内の残差的な上乗せはどの程度か。

Milestone 2はRQ4にmixedな答えを与えたが、推論上の留保が残る。RQ5・RQ6が
未成立なら、論文の中心命題はRQ1〜RQ4に限定する。RQ7に対するE1の答えは
探索的・記述的なside resultとして扱い、確認命題や因果命題へ格上げしない。

## 予定する貢献

- 内部介入と表層観測を混同しない、能力認識型の実験ハーネス
- モデル、リビジョン、dtype、介入点を固定した MLX–Transformers パリティゲート
- ゼロ介入、ランダム直交方向、符号反転、用量反応、ラベル置換を統合した前因果的スクリーニング
- シードを独立標本として数えず、ターゲットをクラスタとして扱う推論設計
- 正セルと非正セルを同時に報告する、主張境界付きの公開アーティファクト

「絵文字の意味を発見した」は貢献に含めません。

## 論文構成

### 1. Abstract

- 問題: 内部方向の解釈は、再現性とスカラー統制より先に語られがち
- 方法: 固定グリフパネル、ターゲット、ランダム対照、バックエンドパリティ
- 結果: 確認実験で事前指定した主要評価量のみ記載
- 限界: 条件依存性、トークン化、標本単位、因果性
- 結論: 成立した最小限の命題だけを一文で述べる

### 2. Introduction

- 絵文字・グリフを、小さく制御しやすい介入パネルとして使う理由
- 「意味の解釈」より「再現可能な差の有無」を先に問う理由
- 前因果的地図と因果説明の区別
- 研究質問と貢献

### 3. Related Work

- activation steering / representation engineering
- mechanistic interpretability と activation/path patching
- 方向安定性、表現幾何、出力指紋
- トークン化交絡と多言語・記号表現
- Apple silicon / MLX での再現可能な推論

先行研究は、英語原稿の着手時に改めて検索し、一次資料を中心に引用します。

### 4. Methods

- 5色 × 2形状のグリフパネル
- ソースラッパーと方向推定
- 探索段階の24ターゲットと、確認段階の凍結済み48 P2ターゲット。どちらも6群のクラスタ構造
- レイヤー 2 / 4 / 7 / 9 と3段階のRMS強度
- `resid_post` への加算介入
- CountSketchによる出力差分指紋
- ランダム方向、ゼロ、一般絵文字、符号反転、用量、ラベル置換
- 確認段階のトークン数・パネル接頭構造matched controls。Iso-KLは未実施
- 凍結済み主要評価量、target-cluster再標本化、Holm補正、prototype依存感度
- E1のtoken-isomorphic panel、全family-pair transfer、replicate内でのLOTO prototype再構築。確認仮説familyとは分離する

### 5. Backend Validation

- GPT-2リビジョンとFP32を固定
- 4種類のプロンプト長 × 4レイヤー
- トークン、基準ロジット、活性化、ゼロ・非ゼロ介入の一致条件
- 80 / 80検査結果
- エンドツーエンド速度: 17.517 ms 対 10.727 ms、1.633倍（記録時の環境・負荷条件）
- Matched-null Aのforeground processが、高負荷下で798行の時点に外部中断され、その後、重複・欠損・error・非ゼロのzero-hook RMSなしでsealを保った正確なresumeを完了したという実行時の来歴。この負荷事象を、モデルに関する証拠や一般化できる速度結果として扱わない
- この検証を別モデルや別フック点へ一般化しないこと

### 6. Results

結果は、次の順に並べます。

1. 介入量とゼロフックの忠実性
2. ソース方向の反復安定性
3. 指紋優位量の全分布
4. シード横断の再現性
5. レイヤー・強度・ターゲット群別の不均一性
6. 用量反応と符号反転
7. トークン数・接頭構造matched controlsと感度分析
8. 因果実験を行った場合は、アブレーションと復元
9. E1の全family-pair transfer行列、family固有の小さな超過、全family区間、random-controlの不均一性、成立しなかったlayer 4 negative comparator

最大セルは主結果にしません。25 / 36の正セルと11 / 36の非正セルを同じ図に載せます。

Milestone 2では、探索96次元のpaired median difference `+0.047427`を記述値として示し、48 / 32 / 24次元の`+0.040200 / +0.028907 / +0.048591`は同一seedの代数的foldであってseed感度ではないと明記する。「何%を説明したか」は報告しない。

確認表には、layer 2の頑健判定とlayer 4の未解決判定を、主要ソースと独立ソースの両方について並べる。V1のCLI順序によるrole bindingと別監査、固定prototype bootstrapと事後prototype再構築感度を分けて示す。Panel Cの`🟥`、完了した末尾token診断と接頭構造均一化診断も、事後的・記述的な境界とともに省略せず示す。

E1は探索side resultとして別枠に置く。Milestone 2のstatusや因果候補を
強める根拠には使わない。

### 7. Discussion

- 再現可能な出力指紋候補が何を示し、何を示さないか
- 集約効果とセル間不均一性の両立
- トークン化、プロンプト分布、モデル固有性の可能性
- 因果実験の成否に応じた解釈
- グリフを使った制御パネルの利点と限界
- E1で見えた広いfamily間transferと小さなfamily固有超過を、共有token構造で説明できる範囲

### 8. Limitations

- GPT-2の単一リビジョンから始めたこと
- 標準実験をMLXだけで完走したこと
- シードは反復推定で、独立観測ではないこと
- ターゲットが設計された24件で、自然分布の無作為標本ではないこと
- 中立グリフとのトークン長差
- Milestone 2のmatched panelはtoken identityではなく、token countとパネル単位のprefix構造を揃えた対照であること
- E1ではfamily identityと中間GPT-2 tokenが完全に交絡し、第1・第3 tokenを共有しているため、意味上またはtokenizer非依存のfamily表現を同定できないこと
- C1 v1の完全な1レコードが、実験に使われないまま研究agentの文脈へ露出したこと。Bankは廃止済みで、将来の因果実験には新しいversionのbankが必要であること
- v1 analyzerがCLI順序でroleを割り当て、別のinput-binding auditで凍結済み入力との対応を補ったこと
- v1 bootstrapがprototypeをreplicate内で再構築せず、依存対応感度分析が事後的であること
- 置換p値の有限下限と多重性
- 生台帳を公開Gitリポジトリから省略すること
- 未実施のフック点、SAE、生成、パス因果

### 9. Reproducibility and Artifact Availability

- コード、固定設定、入力、依存バージョン
- バックエンドパリティレシート
- 標準実験レシートとアーティファクト整合性監査
- 公開集約データとハッシュ付きマニフェスト
- E1のtokenizer preflight、全記述解析、5つの軽量run bundle、root manifest
- 省略した約74 MiB（77.3 MB）の生台帳・NPZを再生成する手順
- 英語・日本語の対文書

## 予定する図表

1. **Figure 1:** 実験フローと主張レベル
2. **Figure 2:** グリフパネル、方向推定、ターゲット介入
3. **Figure 3:** 36セルすべての指紋優位量
4. **Figure 4:** シード横断再現性とランダム方向対照
5. **Figure 5:** 用量反応、符号反転、iso-KL感度分析
6. **Figure 6:** 因果実験が成立した場合のアブレーション・復元
7. **Table 1:** 固定設定とバックエンドパリティ
8. **Table 2:** 主要評価量、区間、正・非正セル
9. **Table 3:** 追試モデルと成立・不成立範囲
10. **Figure / Supplement:** E1のlayer別5 × 5 transfer行列。確認結果とは明確に分ける

Milestone 2の主表には、主要ソースlayer 2（+0.208363、[0.137463, 0.276893]、Holm p = 0.00143999）とlayer 4（-0.0329465、[-0.0761085, 0.0110094]、未解決）、独立ソースlayer 2（+0.187507、[0.125489, 0.247659]、p = 0.00393996）とlayer 4（-0.086379、[-0.159246, -0.016917]、未解決）をすべて載せる。

## 主張の語彙

### 現段階で使用できる

- reproducible fingerprint candidate
- aggregate separation from random-direction controls
- pre-causal activation screening
- condition-dependent / heterogeneous effect
- robust to the prespecified token-count and token-prefix matched controls at layer 2 under frozen v1
- exploratory matched-slot recurrence under a fixed middle-token family substitution

### 追加の証拠なしには使用しない

- semantic representation
- concept encoded by the glyph
- circuit for color or shape
- causal path
- universal or model-independent effect
- semantic emoji family, tokenizer-independent E1 effect, layer-specific E1 effect

## 残る論文ゲート

- C1 v1の露出文脈の外で新しいversionの因果bankを用意し、それを開く前にlayer 2を対象とする完全な因果プロトコルを凍結する。プロトコル設計の着手だけを目的とした追加bankは求めない。
- 論文での最終的な確認表現と、それを支える再現実験では、v1のrole bindingとprototype再標本化依存に事前に対処する。
- 正負を問わず、事前指定した因果実験を少なくとも1件完了する。新しいbankを早く開かない。
- 独立backendの実装確認と、最終主張に見合う別modelまたはtokenizerでの再現を完了する。
- 完全なraw evidenceをarchiveし、checksumを付ける。
- 論文の表と図をversion管理したscriptから生成する。
- 先入観のない再現性・主張境界レビューを行う。
- 英語原稿と日本語公開概要の命題を一致させる。
- E1の記述区間にp値、確認status、layer比較の推論を後付けしない。

現段階では、完成原稿を主張しない。英語論文がPhase Iの終点である。

## 執筆開始前のチェック

- 新しいversionのbankを開く前に、layer 2の候補、介入、endpoint、対照、多重性familyを因果プロトコルへ凍結したか
- 主要評価量と多重性管理を事前固定したか
- 実行したトークン数・接頭構造matched controlsと、事後的・記述的な二次診断を正確に区別したか
- 正・非正・失敗セルをすべて表に入れたか
- 論文中の数値が、公開レシートまたは集約アーティファクトへ一意にたどれるか
- 因果語の強さが、アブレーションと復元の結果を超えていないか
- 英語本文と日本語概要の命題が一致しているか
