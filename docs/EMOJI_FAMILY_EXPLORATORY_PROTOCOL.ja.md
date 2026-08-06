# E1 探索プロトコル: トークン同型な絵文字familyのスクリーニング

[English](EMOJI_FAMILY_EXPLORATORY_PROTOCOL.md) · [研究ロードマップ](ROADMAP.ja.md) · [科学的契約](SCIENTIFIC_CONTRACT.ja.md)

プロトコルID: `glyphprobe-e1-token-isomorphic-emoji-families-v1`

## 位置づけと問い

E1は、範囲を限定した探索用のside trackである。3 tokenからなる絵文字について、中間tokenだけが異なる5つのUnicode blockを用意し、slot固有の出力fingerprint分離がblockをまたいで繰り返されるかを調べる。

以下の科学的な選択は、E1のactivation結果を見る前に固定する。実行条件の凍結が完了するのは、この英日文書、panel file、run configuration、tokenizer audit、解析code、environment/model receipt、checksum manifestを、1つの公開commitで結び付けた時点である。それまでは実行状態を`freeze_pending`とする。

E1はMilestone 2の確認実験でも、C1因果実験でも、独立backendによる再現でもない。P2、P3、C1、頑健性、有意性、論文gateのstatusは一切付与しない。

## 固定する絵文字block

各範囲には、両端を含めて10 code pointが入る。Family名は報告時の識別子にすぎず、検証対象となる意味ラベルではない。

| Family ID | Unicode block（両端を含む） | 固定GPT-2での先頭2 token | Slot数 |
|---|---|---:|---:|
| `sky` | `U+1F311`–`U+1F31A` | `[8582, 234]` | 10 |
| `food` | `U+1F351`–`U+1F35A` | `[8582, 235]` | 10 |
| `animals` | `U+1F411`–`U+1F41A` | `[8582, 238]` | 10 |
| `transport` | `U+1F691`–`U+1F69A` | `[8582, 248]` | 10 |
| `social` | `U+1F911`–`U+1F91A` | `[8582, 97]` | 10 |

実行条件を凍結した後は、family、code point、slot順、表示名を追加・削除・並べ替え・改名してはならない。Null、負、不均一な結果も含め、5 familyすべてを公開結果に残す。

## Token-isomorphismの条件

Family \(k\)の対応slot \(j\)について、glyph単体のtoken列は次の形でなければならない。

\[
\operatorname{tokens}(k,j) = [8582,\ m_k,\ r_j].
\]

先頭tokenは全glyphで`8582`とする。Familyごとの中間token \(m_k\)は、上表のとおり`234`、`235`、`238`、`248`、`97`のいずれかである。Code pointの昇順に並べた第3 token \(r_j\)は`239`から`248`までであり、対応するslotでは5 familyすべてで一致しなければならない。したがって、各glyphは必ず3 tokenであり、同じslotをfamily間で比較したときに変わるのは中間tokenだけとなる。

Modelのforwardを始める前に、すべてのcode pointについて、UTF-8 byte列、decode round trip、glyph単体のtoken ID列、source wrapper内でのtoken位置profileをtokenizer auditへ記録する。3 tokenでないglyphがある、familyのprefixが上表と異なる、対応slot間で第3 token IDが異なる、wrapperによってfamily依存のtoken数・介入位置・外側tokenが生じる、という条件のいずれかに当たれば、auditはfail closedとする。

これは、固定した1 tokenizerに対する厳密な構造一致であり、tokenizationの影響を除いた比較ではない。設計上、family identityと中間token IDは完全に交絡している。さらにmatched-slot transferは、意図的に共通化した第1・第3 token IDだけでも説明できる。したがってE1が測るのは、統制した中間token置換の下での反復であり、絵文字の意味やtokenizer非依存のglyph特性ではない。

## 固定するデータの役割

- Target: [`prestage_targets.jsonl`](../data/targets/prestage_targets.jsonl)の先頭24行だけを使う。既存の`continuation`、`factual`、`reasoning`、`procedural`、`classification`、`planning`という6 groupから、それぞれ4 targetで構成される。
- Source context: [`source_wrappers.jsonl`](../data/wrappers/source_wrappers.jsonl)の16行をすべて使う。
- Targetの位置づけ: この24 targetは、すでに探索に使われている。E1でも探索専用として再利用し、未使用または確認用とは表現しない。
- 使用禁止のinput: P2 target bankと、封印中のC1 target bankは、読み込み、tokenize、score、sampleのいずれも行わない。Model、tokenizer、panel、endpoint、解析方法の選択にも使わない。

実行条件の凍結では、target IDとgroup labelの順序、wrapper IDの順序、各fileのhash、最大読込行数を明示的に結び付ける。Source fileへ行が追記されても、E1の対象が暗黙に増えてはならない。

## 固定するmodelと介入cell

E1で使うmodel/runtime familyは1つに限定する。

- model: `openai-community/gpt2`
- revision: `607a30d783dfa663caf39e06633721c8d4cfcd7e`
- backendと演算精度: MLX、FP32
- 実行時のtokenization: `backend.add_special_tokens: false`
- capture site: `resid_post`
- source anchor、capture position、intervention position: `last_nonpad`
- attention capture: 無効（`capture.return_attentions: false`）
- 入力形式: emoji入力は`{emoji}\n{prompt}`、neutral baselineは`{prompt}`とし、system promptは設定しない。
- layer: 2と4のみ。Layer 2をprimary exploratory row、layer 4を事前指定したsecondary negative comparatorとする。
- intervention strength: 0.05のみ
- source-direction seed: 101、211、307
- random control: 各layerにつきrandom direction 2本
- integrity/control switch: zero hookを有効にし、neutral-direction armとsign-flip armは無効にする。

既存のsource-wrapper subsampling ruleとfingerprint構築法を維持し、実行configのhashで固定する。Direction seedはtarget内の反復推定であり、独立標本ではない。Random directionはcontrol rowであって、target数には加えない。Zero hookは実装のintegrity checkであり、E1のendpointではない。結果を見た後で、layer、strength、seed、tokenizer、fingerprint設定、familyを選び直したり、追加条件で救済したりしない。

## 探索endpoint

Family \(k\)、slot \(j\)、target \(t\)、source-direction seed \(s\)に対する、単位長へ正規化した出力fingerprintを\(f_{k,j,t,s}\)とする。事前に指定したtarget groupを\(c(t)\)と表す。Prototypeはすべて、1つのtarget groupを丸ごと除くLOTO（leave-one-target-group-out）で作る。

\[
q_{k,j,-c,s}=\operatorname{unit\_mean}\{f_{k,j,u,s}:c(u)\ne c\}.
\]

評価するfamilyを\(f\)、prototypeを作るfamilyを\(g\)とし、matched-slot scoreを、対応slotとのcosineから対応しない9 slotとのcosine平均を引いた値として定義する。

\[
M_{f\leftarrow g,t,s}=\frac{1}{10}\sum_j\left[\cos(f_{f,j,t,s},q_{g,j,-c(t),s})-\frac{1}{9}\sum_{\ell\ne j}\cos(f_{f,j,t,s},q_{g,\ell,-c(t),s})\right].
\]

対角成分\(M_{f\leftarrow f}\)がwithin-family separationである。非対角成分\(M_{f\leftarrow g}\)、\(g\ne f\)はcross-family shared-suffix transferであり、row \(f\)のfingerprintをrow \(g\)のLOTO prototypeで評価する。まず、各targetの内側で3 seedを平均する。

\[
\bar M_{f\leftarrow g,t}=\frac{1}{3}\sum_s M_{f\leftarrow g,t,s}.
\]

次に、rowごとのtransfer超過量を求める。

\[
R_{f,t}=\bar M_{f\leftarrow f,t}-\operatorname{median}_{g\ne f}\bar M_{f\leftarrow g,t}.
\]

Familyを等しく重み付けしたtarget単位のglobal値は、次のとおりとする。

\[
R_{\mathrm{global},t}=\frac{1}{5}\sum_f R_{f,t}.
\]

Target単位の量を\(Z_t\)とすると、primary descriptive aggregateは、24 targetを等しく重み付けした平均\(\bar Z=24^{-1}\sum_t Z_t\)とする。E1では、target平均による5×5の\(M\)行列全体、5つの\(R_f\)、\(R_{\mathrm{global}}\)を報告する。都合のよいfamily、向き、非対角pairを選んでprimary resultとはしない。Layer 2の平均\(R_{\mathrm{global}}\)をprimary exploratory summaryとし、layer 4は事前指定したsecondary negative comparatorとする。Target medianとtarget group別分布は、secondary descriptionとしてのみ併記できる。各layerのrandom direction 2本はcontrolとして報告し、target数を水増しする用途には使わない。

## 記述的な不確実性

不確実性の表示には、target groupで層化したbootstrapを20,000回用いる。各replicateでは、固定済み6 groupのそれぞれから、4 targetを復元抽出する。Family、layer、endpoint、family pairの比較をpairedのまま保つため、抽出したtarget indexはすべての条件で共有する。

データから推定するLOTO prototypeは、replicateごとに、そのreplicateで復元抽出した非holdout groupから作り直す。全データで作ったprototypeをbootstrap内で再利用してはならない。Seedはtargetの内側に入れたままとし、独立単位として再標本化しない。

各replicateの内側で、\(M\)行列全体、5つの\(R_f\)、family等重みの\(R_{\mathrm{global}}\)を再計算し、targetの等重み平均を求める。各cellについて、観測targetの平均と、20,000回のbootstrap replicate meanの2.5・97.5 percentileを公開する。Target medianとtarget group別分布はsecondary descriptionとして併記できる。さらにfamily pairの完全な行列も示す。Bootstrap seedと実装hashは、E1の最初のmodel forwardより前に、実行manifestへ固定する。

これらの区間は記述目的に限る。E1ではp値、多重性補正付きの判定、同等性検定、`robust`、`confirmed`、`significant`などのstatusを算出しない。

## 停止規則と公開規則

凍結したgridは1回だけ実行する。実行が中断した場合は、封印済みrowからresumeできる。ただし、結果に応じてfamily、layer、strength、seed、endpoint、targetを追加または交換してはならない。避けられない逸脱はversionを分けて開示し、別解析として扱う。凍結済みE1結果を上書きしない。

実行条件の凍結後は、次の項目を公開する。

1. 5 familyすべてのpanelとtokenizer audit
2. configuration、provenance、validation、integrityの各receipt
3. \(M\)行列全体、5つの\(R_f\)、\(R_{\mathrm{global}}\)
4. null、負、不均一、失敗したcell
5. 20,000回の記述的bootstrap出力と解析code
6. 中断、resume、除外、逸脱の記録

## 主張の境界と次の判断

正の結果が得られた場合でも、認める表現の上限は、**固定済みGPT-2 MLX FP32介入cell 1件において、familyごとに中間tokenだけを置換した条件で観測された、探索的なmatched-slot fingerprintの反復**である。

E1から、意味category、familyに依存しない絵文字表現、因果局在、tokenizer非依存性、model間の一般性、backend再現、行動上の意味は導けない。また、色付き図形向けのfactor診断はE1に適用しない。Color、shape、family factor、slot factor、interactionのstatusは付与しない。

E1はMilestone 2の判定を更新せず、C1の介入点を選ばず、C1を開かず、Phase I論文gateも満たさない。E1から焦点を絞った仮説を作る場合は、P2でもC1でもない、新しい未使用target bankと公開プロトコルが必要になる。そのbankへアクセスする前に、確認用prototype、endpoint、hypothesis family、多重性規則、判定境界を凍結する。
