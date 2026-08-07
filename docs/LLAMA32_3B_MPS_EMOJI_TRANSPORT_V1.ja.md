# E2 Llama 3.2 3B MPS 絵文字transportプロトコル v1

[English](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1.md) · [E1プロトコル](EMOJI_FAMILY_EXPLORATORY_PROTOCOL.ja.md) · [MLX numeric screen結果](LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.ja.md) · [ホールドアウトの状態](HOLDOUT_STATUS.ja.md) · [科学的主張の契約](SCIENTIFIC_CONTRACT.ja.md)

Protocol / analysis ID: `glyphprobe-e2-llama32-3b-mps-emoji-transport-v1`

## 位置づけと目的

この文書は、Llama 3.2 3Bによる範囲限定の絵文字transport studyを、Transformers/MPS経路で実行するための条件を事前に固定する。E1で定義したmatched-slot出力fingerprint構造が、固定済みの、より大きなmodel cellでも現れるかを調べる。さらに、個別にcenteringしたtokenizer同型の感度armで、同じ傾向が記述的に保たれるかを確かめる。

以下の科学的な選択は、studyで最初のmodel forwardを行う前に公開しなければならない。凍結は2段階で行う。まず、1つの公開static-freeze commitで、この英日文書、10件のconfig、10件のpanel binding、固定済みanalyzer、test、正確なenvironment/model artifact、preflightの期待値、checksum manifestを結び付ける。このcommitまでは`freeze_pending`とする。次に、そのcleanかつpush済みのcommitからmodel forwardを伴わないtokenizer preflightを実行し、そのreceiptだけを変更した子commitとして公開する。Receiptが合格して公開されるまでは`preflight_pending`であり、実行しない。Static-freeze commitから実行までの間に、設計、code、文書、inputを変更してはならない。

実際のoutcomeを取得するものの、位置づけは探索的なtransport studyである。24 targetは以前の探索ですでに使っている。独立targetによる確認実験、因果実験、意味の検定ではない。Model scale、tokenizer、architecture、backend、演算精度のいずれか1要因だけを切り分ける設計でもない。

## 経路の選定とMLX no-goとの関係

先行するStage-A3 engineering screenでは、固定した2候補がいずれも同じmachine上のspeed gateに失敗し、MLX runtime dtypeは選ばれなかった。そこで本studyでは、Transformers/MPS FP32を用いる新しい科学cellを、別versionとして定義し、上記の2段階で凍結する。失敗したspeed thresholdの緩和でも、MLX fallbackでも、MLX結果の読み替えでもない。

Stage A3のengineering promptでは、FP32のwithin-backend intervention fidelityが高かった。ただし、cross-backend parityの完全なfamilyは実行していない。本プロトコルは、その観測をMLX経路の適格判定へ格上げせず、科学gridでMLXを呼び出さない。将来MLXでstudyを行うなら、engineeringと科学実験の双方に新しいversionのプロトコルが必要になる。

## 固定するmodel、artifact、runtime

| 項目 | 固定値 |
|---|---|
| Backend | `transformers` |
| Model | `mlx-community/Llama-3.2-3B-bf16` |
| Revision | `60a99aaf43164077157d64bf909b7b61143c6a6d` |
| 保存weightのdtype | BF16 |
| Runtime parameter dtype | FP32（`float32`） |
| Device | Apple Metal Performance Shaders（`mps`） |
| Load条件 | `local_files_only: true`、`trust_remote_code: false` |
| Tokenizer surface | `add_special_tokens: false`。chat templateとsystem promptは使わない |
| Architecture identity | 28 layer、width 3,072、vocabulary 128,256、parameter 3,212,749,824 |
| Artifact identity | 9 file、6,434,705,789 byte |
| Artifact manifest SHA-256 | `dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4` |

RuntimeをFP32にしても、保存済みBF16 weightに含まれない情報が増えるわけではない。結果は「BF16 artifactをFP32 runtime parameterで評価した」と記述し、元からFP32 weightのmodelだったとは表現しない。

実行条件の凍結では、実際に使うenvironmentも厳密に結び付ける。適格性を確認したlocal reference environmentは、Python 3.13.13、`glyphprobe` 0.1.0、NumPy 2.4.4、PyTorch 2.11.0、Transformers 4.57.6、arm64上のmacOS 26.2である。Outcomeへアクセスする前に公開freezeへ明示的に組み込まない限り、package、OS、hardware、model file、tokenizer fileの差は、新しいversionのcellを必要とする。最終receiptには、environment全体、MPS availability、model file hash、tokenizer identity、解決後のparameter dtype、source tree hashを記録する。

## 固定するデータの役割とholdout境界

- Targetは、[`prestage_targets.jsonl`](../data/targets/prestage_targets.jsonl)の先頭24 recordに限る。`continuation`、`factual`、`reasoning`、`procedural`、`classification`、`planning`の6 groupから各4件を、file内の順序どおり使う。
- この24 targetは、すでに探索で使ったものだ。未使用、holdout、確認用とは呼ばない。
- 同fileの25件目以降は、本プロトコルの対象外とする。
- Source contextは、[`source_wrappers.jsonl`](../data/wrappers/source_wrappers.jsonl)の16 recordすべてを、固定順序のまま使う。
- P2とC1は、実行面にも解析面にも入れない。本studyでは、読み込み、sampling、tokenize、model forward、score、選択のいずれにも使わない。
- C1 v1は、研究文脈への検索露出を受けて退役済みであり、未使用bankではない。根拠となる記録は、[ホールドアウトの状態](HOLDOUT_STATUS.ja.md)と[機械可読の事故記録](../validation/holdout_exposure_incidents/2026-08-07-repository-search.json)である。

Prestage file全体のSHA-256は`91ec5138c31ba56aede5f94d11a43b460385015237f437d933a55be3bc775ad7`、順序付き先頭24件のSHA-256は`26d42a9be61d9b6a28acf18f18b9b1d771f0f4531b3a576112ba0f6add76713b`、16 wrapper fileのSHA-256は`310af508fbe1dd218cb72552d614c812d5afc2bca34165433036f1058a20bdee`である。

Freeze manifestには、target IDとgroup labelの順序、wrapper IDの順序、file hash、行数上限を固定する。Source fileへrecordが追記されても、studyの範囲を暗黙に増やしてはならない。

## 個別にcenteringする2つのarm

2つのarmは別々に実行する。同じrunの結果から一方をfilterして作ってはならない。

| Arm | Familyごとの有効slot | Glyph数 | Panel source | 役割 |
|---|---:|---:|---|---|
| `full50` | `slot_00`--`slot_09` | 50 | 既存E1の10 glyph panel 5件 | Primary literal panel |
| `core35` | `slot_03`--`slot_09` | 35 | 固定済みE2の7 glyph panel 5件 | Tokenizer同型の感度arm |

Family順は`sky`、`food`、`animals`、`transport`、`social`とする。Family名は報告用のregistry labelであり、この実験によって成立する意味変数ではない。

`full50`のconfigは次の5件である。

- [`e2_llama32_3b_mps_full50_sky_v1.yaml`](../configs/e2_llama32_3b_mps_full50_sky_v1.yaml)
- [`e2_llama32_3b_mps_full50_food_v1.yaml`](../configs/e2_llama32_3b_mps_full50_food_v1.yaml)
- [`e2_llama32_3b_mps_full50_animals_v1.yaml`](../configs/e2_llama32_3b_mps_full50_animals_v1.yaml)
- [`e2_llama32_3b_mps_full50_transport_v1.yaml`](../configs/e2_llama32_3b_mps_full50_transport_v1.yaml)
- [`e2_llama32_3b_mps_full50_social_v1.yaml`](../configs/e2_llama32_3b_mps_full50_social_v1.yaml)

`core35`のconfigは次の5件である。

- [`e2_llama32_3b_mps_core35_sky_v1.yaml`](../configs/e2_llama32_3b_mps_core35_sky_v1.yaml)
- [`e2_llama32_3b_mps_core35_food_v1.yaml`](../configs/e2_llama32_3b_mps_core35_food_v1.yaml)
- [`e2_llama32_3b_mps_core35_animals_v1.yaml`](../configs/e2_llama32_3b_mps_core35_animals_v1.yaml)
- [`e2_llama32_3b_mps_core35_transport_v1.yaml`](../configs/e2_llama32_3b_mps_core35_transport_v1.yaml)
- [`e2_llama32_3b_mps_core35_social_v1.yaml`](../configs/e2_llama32_3b_mps_core35_social_v1.yaml)

### Llama tokenizerの条件

本studyのmodel forwardを始める前に、special tokenなしのglyph単体auditで、次の条件を厳密に検証する。

- `full50`の50 glyph中47件は、3 tokenの`[9468, m_k, r_j]`となる。
- 固定family順の中間token \(m_k\)は、`234`、`235`、`238`、`248`、`97`である。
- 通常のslot `00`--`09`に対応する第3 token \(r_j\)は、`239`--`248`である。
- `full50`に含まれる2 tokenの例外は、`🌒 -> [9468, 102032]`、`🌓 -> [9468, 107569]`、`🤑 -> [9468, 100701]`の3件だけである。
- `core35`の35 glyphは、すべて厳密に`[9468, m_k, r_j]`となる。Slot `03`--`09`では、5 familyが第3 token `242`--`248`を共有する。

Auditには、code point、UTF-8 byte、decode round trip、glyph単体のtoken ID、各source wrapper内での位置profileも記録する。Family依存のwrapper token数、anchor、介入位置、外側tokenを含め、いずれかが固定条件と異なればfail closedとする。

`core35`がtokenizer同型なのは、このtokenizerと入力構成に固定した場合だけである。Tokenizationによる説明を排除できる設計ではない。Familyと中間tokenのidentityは交絡したままで、第1 tokenと対応する第3 tokenは意図的に共有している。

### Armごとにpanel centeringを独立させる

Arm、family、layer、direction seedごとに、固定済み`wrapper_subsample`実装が16 wrapperから12件を非復元抽出する。Arm \(a\)、family \(k\)、slot \(j\)、seed \(s\)、layer \(l\)におけるsource activation平均を\(\bar h_{a,k,j,s,l}\)とすると、介入directionは次のとおりである。

\[
d_{a,k,j,s,l}=\bar h_{a,k,j,s,l}-\frac{1}{|J_a|}\sum_{u\in J_a}\bar h_{a,k,u,s,l}.
\]

したがって、`full50`ではfamilyごとに10 glyphでcenteringし、`core35`では7 glyphを使ってcenteringし直す。Random directionも、各armで有効なpanel-direction spanに基づいて作り、そのspan成分を除く。`full50`を実行した後でfingerprint、direction、random controlを部分抽出し、`core35`の結果として扱ってはならない。

Config上のneutral glyphは`🟰`である。`centroid_mode`は`panel`なので、neutralはsource inventoryとgeneric-emojiの記録には入るが、介入centroidには使わない。Generic direction自体も実行しない。

## 介入・計測cellの固定値

10件のconfigは、次のcellを共有する。

| 要素 | 固定値 |
|---|---|
| Mode | internal activation intervention |
| Capture / intervention site | `resid_post` |
| Layer | `[5, 11]` |
| Position | source anchor、capture、interventionのすべてで`last_nonpad` |
| 実際のinternal input | sourceは、固定wrapperの`{emoji}`をglyphまたは`🟰`へ置換する。Targetはraw `{prompt}`を使う |
| Config上のsurface専用field | emojiは`{emoji}\n{prompt}`、neutralは`{prompt}`、`system_prompt: null`。Internal modeでは使わない |
| Attention capture | false |
| Operation | activation addition |
| Direction normalization | RMS |
| Strength | `0.05`のみ |
| Clip | global RMS。perturbation / target RMS比の上限`0.25` |
| Direction seed | `[101, 211, 307]` |
| Replicate rule | `wrapper_subsample`、fraction `0.75`、16 wrapper中12件 |
| Run behavior | `resume: false`、`fail_fast: true`、`deterministic_torch: false`、解決後の`max_errors: 10` |
| Random control | layer / seedごとに2本。有効なpanel span成分を除く |
| Zero hook | target / layerごとに1回。integrity確認に限る |
| 無効にするcontrol | sign flip、label shuffle、neutral direction、iso-KL、SAE |
| Output fingerprint | 96次元、CountSketch seed `8675309`、保存する |
| Distribution summary | top-k `50`、RBO `p=0.90`、top logit delta `32`、epsilon `1e-12` |
| Split-half診断 | 200回 |
| Generation | 実行しない |

`targets.calibration_cases`は6として解決されるが、iso-KLを無効にするため、calibration forwardもendpointも生じない。Primary layerは5だけである。Layer 11は事前指定したsecondary depth comparatorであり、negative controlではない。V1では、他のsite、layer、strength、seed、fingerprint次元、tokenizer、prompt surface、generation設定を追加しない。

## 実行回数

Panelとcellから、実行回数を次のとおり固定する。

| Arm | Source forward | Target baseline | Glyph intervention | Random control | Zero hook | Intervention ledger行 | Forward合計 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `full50` | 880 | 120 | 7,200 | 1,440 | 240 | 8,880 | 9,880 |
| `core35` | 640 | 120 | 5,040 | 1,440 | 240 | 6,720 | 7,480 |
| 合計 | 1,520 | 240 | 12,240 | 2,880 | 480 | 15,600 | 17,360 |

1 familyあたり、`full50`は1,976 forward、1,776 intervention row、`core35`は1,496 forward、1,344 intervention rowとなる。Gridはarmとfamilyを組み合わせた10 runすべてで構成する。Callの不足、重複、余分な実行があればcompleteness違反とし、分母を調整して救済しない。

## Endpointの定義

\(a\in\{\texttt{full50},\texttt{core35}\}\)とし、\(J_a\)を各armの10または7個の順序付きslotとする。Arm \(a\)、family \(k\)、slot \(j\)、target \(t\)、direction seed \(s\)、layer \(l\)に対する、intervention後logitからbaseline logitを引いた差の96次元CountSketchを単位長へ正規化し、\(f_{a,k,j,t,s,l}\)と表す。固定済みtarget groupを\(c(t)\)とする。

Prototypeはすべて、1つのtarget groupを丸ごと除くLOTO（leave-one-target-group-out）で作る。

\[
q_{a,k,j,-c,s,l}=\operatorname{unit\_mean}
\{f_{a,k,j,u,s,l}:c(u)\ne c\}.
\]

評価するfamilyを\(f\)、prototypeを作るfamilyを\(g\)としたとき、matched-slot scoreを次のように定義する。

\[
M_{a,f\leftarrow g,t,s,l}=\frac{1}{|J_a|}\sum_{j\in J_a}
\left[
\cos(f_{a,f,j,t,s,l},q_{a,g,j,-c(t),s,l})
-\frac{1}{|J_a|-1}\sum_{u\in J_a,u\ne j}
\cos(f_{a,f,j,t,s,l},q_{a,g,u,-c(t),s,l})
\right].
\]

対応しないslotの平均に使う分母は、`full50`で9、`core35`で6となる。まず、各targetの内側で3つのdirection seedを平均する。

\[
\bar M_{a,f\leftarrow g,t,l}=\frac{1}{3}\sum_s M_{a,f\leftarrow g,t,s,l}.
\]

Familyごとのcross-family transfer超過量と、family等重みのglobal値は、次のとおりとする。

\[
R_{a,f,t,l}=\bar M_{a,f\leftarrow f,t,l}
-\operatorname{median}_{g\ne f}\bar M_{a,f\leftarrow g,t,l},
\qquad
R_{a,\mathrm{global},t,l}=\frac{1}{5}\sum_f R_{a,f,t,l}.
\]

Targetを集約するときは、固定した24 targetの算術平均を用い、各targetを等しく重み付けする。Direction seedはtarget内の反復推定であり、独立観測ではない。\(R_{\mathrm{global}}\)では5 familyを等しく重み付けする。Target medianとtarget group平均は、secondary descriptionとしてのみ報告する。

## 要素数1のprimary criterion

Primary hypothesis familyは、次の1要素だけで構成する。

`H_E2_1_full50_layer5_R_global_positive`（短縮名`H_E2_1`）: \(R_{\mathrm{full50},\mathrm{global},t,5}\)を24 targetで等重み平均した値が、0より大きい。

事前指定した両側95% percentile bootstrap intervalの下端が、厳密に0を上回る場合に限りcriterionを満たす。Primary familyの要素数は1なので、多重性補正は行わない。Validかつcompleteな実行に付けられるstatusは、次の2つだけである。

- `transport_criterion_met`
- `transport_criterion_not_met`

どちらも`confirmed`、`robust`、`significant`を意味せず、意味的・因果的なstatusでもない。Gridがinvalidまたはincompleteなら、primary statusを付けない。

## Bootstrapとpaired解析

Target groupで層化したbootstrapを、seed `20260808`で正確に20,000回行う。各replicateでは、固定済み6 groupのそれぞれから4 targetを復元抽出する。抽出したtarget indexは、2 arm、全family、2 layer、全endpoint、全ordered family pairで共有する。

データから推定するLOTO prototypeは、replicateごとに、そのreplicateで復元抽出した非holdout groupから作り直す。全データで作ったprototypeをbootstrap内で再利用してはならない。Direction seedはtarget内で平均したまま再標本化せず、独立単位として数えることも禁止する。

公開する各cellには、観測targetの等重み平均と、20,000 replicate meanの2.5・97.5 percentileを記録する。同じpaired replicateから、target単位の`core35 - full50`差も記述的に算出する。この差に判定thresholdは設けず、tokenizationで説明された割合とは呼ばない。

## 必須のsecondary / control出力

次の出力はすべて必須とし、primary resultの救済には使わない。

1. `core35`、layer 5の\(R_{\mathrm{global}}\)、5つの\(R_f\)、完全な5×5の\(M\)行列
2. 2 arm、layer 11の同じ出力。Layer 11はsecondary depth comparatorとして扱う。
3. 2 arm・2 layerの、family固有の全\(R_f\)、対角のwithin-family \(M\)、20件すべてのordered off-diagonal transfer cell
4. \(R_{\mathrm{global}}\)に対するtarget単位のpaired `core35 - full50`差。記述目的に限る。
5. Arm、family、layer、seedの全random-control cell。合計60 cell、2,880 rowとなり、2本のrandom directionと24 target全行を残す。
6. Zero-hookの全行と、run / layerごとのactivation/logit delta RMS最大値。20件のrun/layer cellは、2つの最大値がともに`<= 1e-6`でなければならない。480 rowすべてをrun artifactへ残し、全最大値と各pass/fail値をanalysis receiptへ残す。
7. Direction wrapperの選択、direction/scalar-balance summary、perturbation / target RMS、clip発生率、run error、taskの重複・不足検査、固定したdistribution診断のすべて

`core35` armで`full50`のprimary criterionを救済してはならず、layer 11でlayer 5を救済してもならない。都合のよいfamily、seed、random-control比較、target groupをprimary familyへ昇格させない。Secondary intervalは記述目的に限り、多重性補正付きのstatusを付けない。

## Preflight、実行、停止規則

最初のmodel forwardより前に、no-overwrite preflightを通す。公開freeze、固定sourceのidentity、10件のconfig / panel hash、target / wrapperの順序、tokenizer条件、local model artifact全体のhash、AutoConfig architecture、固定software environment、MPS availability、要求するFP32 / MPS cell、実装 / analyzer hash、予想call数を検証する。このpreflightはlanguage-model weightをloadせず、forwardも0回である。各backend loadでは、最初のforwardより前に、すべてのparameterが実際にFP32であることを追加検証する。Launcherが要求するのは、cleanな`main` worktreeで`HEAD == origin/main`であること、preflightでauditしたcommit以後のtracked changeが固定preflight receiptだけであること、10 cellすべてのrun namespaceとlauncher log namespaceが未作成であることだ。1項目でも失敗すれば、科学実行を始めない。

中間結果にかかわらず、10 configすべてを実行する。固定順は`full50`、`core35`とし、各arm内では`sky`、`food`、`animals`、`transport`、`social`の順に進める。Configごとに独立したPython processを使い、厳密に逐次実行する。2つのfull modelを同時にmemoryへ載せない。10件すべてのrun receiptとledgerをsealしてから、outcome解析を始める。Outcome、経過時間、速度、作業上の都合による停止規則は設けない。Hardware保護または温度上昇による中断は、技術的な中断として扱い、記録する。

最初のprocessの直前に、launcherはimmutableかつno-overwriteのattempt-start receiptを公開し、preflight、manifest、Git authority、空のnamespace、cell順、開始時刻を固定する。完走時のexecution receiptは、そのpathとSHA-256を必須参照する。捕捉できるprocess failureまたは中断では、別のno-overwrite failure receiptを書き、success receiptは書かない。突然停止した場合にも、attempt-start receiptと一意なlauncher namespaceがincomplete markerとして残る。

技術的に中断しても、v1はresumeしない。部分的な証拠は保持し、incompleteと記録する。新しいattemptには、実行前にfreezeした新しいprotocol version、manifest、出力先が必要であり、v1のrowを上書きも再利用もしない。結果を見てからのrerun、MLX fallback、input交換、threshold調整、layer・strength・seed・endpointの追加、選択的な除外は認めない。

Code、config、panel、target、wrapper、tokenizer、model、environment、解析のいずれかを変える場合は、protocol versionと出力先を新しくする。Zero-hook thresholdの不合格はintegrity failureとして扱う。Integrityまたはcompletenessに失敗したときは、primary statusとanalysisの公開を止める。Runとlauncherの証拠は保持し、invalidまたはincompleteと明記する。Outcomeを確認した後で、v1の科学記録を修復しない。

## Artifact公開とno-overwrite条件

公開証拠のrootは、[`artifacts/llama32_3b_mps_emoji_transport_v1/`](../artifacts/llama32_3b_mps_emoji_transport_v1/)とし、`preflight/`、`runs/`、`analysis/`を置く。Tokenizer preflightは`preflight/tokenization_audit_v1.json`へ固定する。Freeze manifestは[`data/manifests/llama32_3b_mps_emoji_transport_v1.json`](../data/manifests/llama32_3b_mps_emoji_transport_v1.json)、launcherが将来no-overwriteで書くexecution receiptは`validation/llama32_3b_mps_emoji_transport_v1/execution_receipt.json`とする。10件のlocal run directoryには、receipt、resolved config/input、tokenizer record、plan、direction replicate、target baseline、raw intervention ledger、fingerprint/scalar-balance summary、report、error、deviation recordを完全に残す。

Gitで公開するbundleは意図的にcompactにする。Large fileを除く検証済みrun fileとanalysis全体を収録し、各runのraw `interventions.jsonl`、`source_activations.npz`、`directions.npz`、`target_baselines.npz`は除外する。No-overwriteのroot manifestで、公開memberすべてをhash固定し、除外したlocal fileすべてについてSHA-256、byte数、row数またはarrayのkey / shape / dtypeを記録する。このhashは解析に使ったlocal artifactを同定するが、除外データを復元できない。完全なreplayには正確な再実行が必要である。

固定analyzerは、次の6 fileのみをanalysis出力として公開する。

| File | 必須行数または役割 | Unique key |
|---|---:|---|
| `panel_target_scores.jsonl` | 480 | `panel_arm`、family、layer、target ID |
| `transfer_target_scores.jsonl` | 1,920 | `panel_arm`、source family、prototype family、layer、target ID |
| `family_cell_summary.jsonl` | 20 | `panel_arm`、family、layer |
| `transfer_cell_summary.jsonl` | 80 | `panel_arm`、source family、prototype family、layer |
| `llama32_3b_mps_emoji_transport_receipt.json` | 判定と来歴を完全に含む機械可読receipt | 1 receipt |
| `report.md` | validかつcompleteなgridについて、primary、secondary、null、負、不均一な結果をすべて記載する。invalidまたはincompleteなgridではanalysis reportを公開しない | 1 report |

480件のpanel-target rowは、2 arm、2 layer、24 targetについて、5 familyの対角cellを収録する。1,920件のtransfer-target rowは、同じarm / layer / target gridについて、20件のordered off-diagonal pairをすべて収録する。両fileを合わせれば、すべての5×5行列を再構成できる。

Publication manifestでは、英日プロトコル、10件のpanel/config、tokenizer preflight、analyzer、test、source tree、model/environment identity、10件のrun payload、6件のanalysis出力、全deviation/error、全file checksumを結び付ける。生成receiptと最終analysis出力はstagingへ作成し、schemaとidentityを検証したうえで、final destinationが存在しない場合に限りatomic renameする。手作業での編集、truncate、overwriteは禁止する。再実行には新しいversionの出力先を使う。

## 主張の境界

Primary criterionを満たした場合でも、認める最も強い表現は次のとおりである。

> 事前に公開凍結した、Transformers/MPSだけを用いるLlama 3.2 3BのFP32 runtime cellにおいて、すでに探索で使った24 target上でmatched-slot出力fingerprint transportを観測した。個別にcenteringしたtokenizer同型の35 glyph感度armも併せて実行した。

満たさなかった場合に認める最も強い表現は、次のとおりである。

> 事前に公開凍結した、Transformers/MPSだけを用いるLlama 3.2 3BのFP32 runtime cellは、すでに探索で使った24 target上で、事前指定したmatched-slot出力fingerprint transport criterionを満たさなかった。個別にcenteringしたtokenizer同型の35 glyph armは、primary resultを救済しない感度解析として扱った。

正の結果が得られても、絵文字の意味、意味family、tokenizer非依存性、familyに依存しないglyph表現、独立targetによる確認、因果局在、generation上の挙動、backendだけを切り分けた再現、model-scale効果は示せない。E1とE2では、weight、tokenizer、vocabulary、architecture、backend、演算精度が同時に変わる。E2の2 arm間でも、glyph構成、panel centering、mismatch集合、random-control spanが異なる。したがって、その差はtokenizationで説明された割合ではない。Targetとwrapperを共有するため、2 armはpaired感度解析であり、独立replicationでもない。

本studyはC1のstatusを更新せず、因果主張を許可せず、Phase Iのreplication gateやcausality gateを単独では閉じない。C1 v1の退役を含むすべての限界は、最終英語論文と証拠packageへ残す。
