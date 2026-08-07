# E2 Llama 3.2 3B MPS絵文字transportプロトコル v2

[English](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.md) · [v1 preflight failure](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.ja.md) · [ホールドアウトの状態](HOLDOUT_STATUS.ja.md) · [科学的主張の契約](SCIENTIFIC_CONTRACT.ja.md)

Protocol / analysis ID: `glyphprobe-e2-llama32-3b-mps-emoji-transport-v2`

## 状態と目的

この英日文書、10件のv2 config、panel binding、v2 preflight、launcher、analyzer、
公開tool、test、正確なenvironment/model artifact、checksum manifestを1つの公開commitで
結び付けるまでは`freeze_pending`とする。そのcleanかつpush済みのcommitから、model
forwardを伴わないpreflightを実行し、
`artifacts/llama32_3b_mps_emoji_transport_v2/preflight/tokenization_audit_v2.json`
だけを変更した子commitとして公開する。Receiptが合格して公開されるまでは
`preflight_pending`であり、実行しない。

V2の問いはv1と同じである。E1のmatched-slot出力fingerprint構造が、固定したLlama 3.2
3B Transformers/MPS FP32 cellでも現れるかを調べ、別にcenteringしたtokenizer同型の
35-glyph感度armで記述的に確かめる。すでに探索した24 targetを再利用するため、実際の
outcomeを取得するが位置づけは探索的である。

## V1 failureとv2で許す唯一の変更

V1はmodel forwardを伴わないtokenizer preflightで停止した。Language modelのweightは
読み込まず、runも科学的outcomeも作っていない。凍結済みauditが、先頭tokenに直前のspaceが
含まれる場合にも、wrapper内のcontextual token IDとoffsetをraw glyphと同一にするよう
誤って要求した。詳細は[v1 failure記録](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.ja.md)に固定した。

V2で変えるのは次の2点だけである。

- raw tokenizationと正確なcontextual tokenizationを分けて検証するtokenizer audit
- protocol、manifest、config、run、receipt、analysis、log、公開先をすべてv2 namespaceへ変更

Model、artifact revision、演算、panel、target、wrapper、layer、site、strength、seed、control、
fingerprint設定、実行順、bootstrap、endpoint、判定規則、主張境界は変えない。最初のmodel
forward前に改めて固定し、outcomeを見た後は変更しない。

## 固定するmodelとenvironment

| 項目 | 固定値 |
|---|---|
| Model | `mlx-community/Llama-3.2-3B-bf16` |
| Revision | `60a99aaf43164077157d64bf909b7b61143c6a6d` |
| Architecture | Llama、28 layers、width 3072、vocabulary 128256 |
| Parameter数 | 3,212,749,824 |
| Backend | raw Transformers |
| Device | MPS |
| Runtime parameter dtype | FP32。最初のforward前に検証 |
| Tokenizer surface | special token、chat template、system promptなし |
| Network | Hugging Face / Transformers offline |

Local model snapshotは9 file、6,434,705,789 byteで、path非依存manifest SHA-256を
`dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`
とする。実行environmentはPython 3.13.13、GlyphProbe 0.1.0、NumPy 2.4.4、PyTorch
2.11.0、Transformers 4.57.6、macOS 26.2 arm64で固定する。差があれば別versionが必要である。

先行するMLX Stage A3のno-goは変わらない。V2は別versionのTransformers/MPS studyであり、
MLX fallbackでも結果の読み替えでもない。

## 固定inputとholdout境界

- Targetは[`prestage_targets.jsonl`](../data/targets/prestage_targets.jsonl)の先頭24件を順序どおり使う。6 target groupから各4件である。
- Source contextは[`source_wrappers.jsonl`](../data/wrappers/source_wrappers.jsonl)の16件を順序どおりすべて使う。
- P2と廃止済みC1 v1は、実行、preflight、analysisの対象外とする。Read、sample、tokenize、model forward、score、selectのいずれにも使わない。

Prestage全体のhashは`91ec5138c31ba56aede5f94d11a43b460385015237f437d933a55be3bc775ad7`、
先頭24件のslice hashは`26d42a9be61d9b6a28acf18f18b9b1d771f0f4531b3a576112ba0f6add76713b`、
wrapper hashは`310af508fbe1dd218cb72552d614c812d5afc2bca34165433036f1058a20bdee`である。

## 固定するpanel arm

| Arm | Slot | Glyph数 | 役割 |
|---|---|---:|---|
| `full50` | `slot_00`〜`slot_09` | 50 | 唯一のprimary arm |
| `core35` | `slot_03`〜`slot_09` | 35 | primaryを救済しないtokenizer構造感度arm |

5 familyは`sky`、`food`、`animals`、`transport`、`social`である。各familyは別processで
実行し、active panel内で個別にcenteringする。`core35`は`full50`の正確な7-slot subsetだが、
独立にrecenterし、random-control spanも作り直す。実行後のsubsetでは作らない。

## 修正して固定するtokenizer contract

Raw glyphのcontractは変えない。

- Full panel 50件中47件は`[9468, m_k, r_j]`
- Family-middle tokenは固定family順に`234`、`235`、`238`、`248`、`97`
- `slot_00`〜`slot_09`の通常suffixは`239`〜`248`
- 3件の2-token例外はpreflightに正確に記録
- Core 35件はすべて`[9468, m_k, r_j]`で、共有suffixは`242`〜`248`

Source wrapper内のcontextual tokenizationは別に固定する。First tokenは、wrapper `w01`、
`w03`、`w04`、`w06`、`w10`、`w12`、`w13`、`w14`、`w15`では`11410`、`w02`、
`w05`、`w07`、`w08`、`w09`、`w11`、`w16`では`9468`とする。Preflightでは省略名ではなく
完全なwrapper IDを結び付ける。

First tokenが`11410`なら、そのoffsetは直前のspaceと絵文字区間だけを正確に覆い、残りの
重複tokenは絵文字区間だけを覆う。`9468`なら、重複tokenはすべて絵文字区間だけを覆う。
Core itemのcontextual spanは`[wrapper_first, family_middle, slot_suffix]`と完全一致させる。
Full50では、raw profileの先頭`9468`だけをwrapper-first tokenへ置き換えたID列と一致させる。
各wrapper内で、coreのpositionと総token数、full-panel例外のtoken数規則、50 glyphすべての
outside-token列を一定にする。Decoded round trip、anchor、code point、UTF-8 byte、800件の
wrapper profileを記録し、違いがあれば実行を止める。

これは固定tokenizerとinput constructionに限った同型性である。Family identityとmiddle tokenは
交絡したままであり、tokenizationによる説明を除去しない。

## 固定する介入cell

| 項目 | 固定値 |
|---|---|
| Mode / site | `resid_post`へのinternal activation addition |
| Layers | `[5, 11]` |
| Position | source、capture、interventionとも`last_nonpad` |
| Strength / normalization | `0.05`、RMS |
| Clip | global RMS、ratio最大`0.25` |
| Direction seed | `[101, 211, 307]` |
| Direction replicate | 16 wrapper中12件、固定0.75 subsample |
| Random control | layer / seedごと2本、active panel spanの外側 |
| Zero hook | target / layerごと1回。厳密なintegrity検査 |
| 無効 | sign flip、label shuffle、neutral direction、iso-KL、SAE、generation |
| Fingerprint | 96次元CountSketch、seed `8675309` |
| 診断 | top-k 50、RBO 0.90、split-half 200、top delta 32 |
| Run policy | `resume: false`、fail fast。v2を再開しない |

Layer 5だけをprimary layerとし、layer 11は事前指定したsecondary depth comparatorとする。
Seedはtarget内にnestedした反復direction推定であり、独立標本には数えない。

## 正確な実行数

| Arm | Source | Baseline | Glyph | Random | Zero | Ledger row | 全forward |
|---|---:|---:|---:|---:|---:|---:|---:|
| `full50` | 880 | 120 | 7,200 | 1,440 | 240 | 8,880 | 9,880 |
| `core35` | 640 | 120 | 5,040 | 1,440 | 240 | 6,720 | 7,480 |
| 合計 | 1,520 | 240 | 12,240 | 2,880 | 480 | 15,600 | 17,360 |

10 cellは別々のPython processで逐次実行する。順序は`full50`、`core35`で、各arm内は
`sky`、`food`、`animals`、`transport`、`social`とする。途中のoutcomeは見ない。捕捉した
failureではno-overwrite failure receiptだけを書き、success receiptは書かない。中断したv2は
incompleteとして廃止し、resume、修復、選択的rerunをしない。

## 固定analysisとprimary判定

保存した96次元fingerprintを、E1のleave-one-target-group-out prototype手順で解析する。
Targetとsource familyごとに、`M`はmatched-family similarity、`R`は4つのmismatched prototype
family similarityの中央値を差し引いた値、`R_global`はfamily等重みの`R`平均である。

唯一のprimary rowは次のとおりである。

- arm `full50`
- layer 5
- endpointはfamily等重み`R_global`
- 両側95% percentile区間の下端が0より厳密に大きい場合だけ`transport_criterion_met`

Bootstrapは20,000回、seed `20260808`とする。6 group内で各4 target promptを再標本化し、arm、
layer、endpoint、paired差に同じjoint scheduleを使う。各replicate内でdata-dependentな
leave-one-group-out prototypeをすべて作り直す。Direction seedはnestedのまま平均する。

Secondaryでprimaryを救済しない出力は、core35 layer 5、両armのlayer 11、family別row、完全な
transfer matrix、random / zero control、target / target-group記述、pairedの記述的
`core35 - full50`差である。この差をtokenizationで説明された割合とは呼ばない。

固定する6つのanalysis出力は次のとおりである。

- `panel_target_scores.jsonl` — 480 row
- `transfer_target_scores.jsonl` — 1,920 row
- `family_cell_summary.jsonl` — 20 row
- `transfer_cell_summary.jsonl` — 80 row
- `llama32_3b_mps_emoji_transport_v2_receipt.json`
- `report.md`

Invalidまたはincompleteな証拠では、analysis公開とprimary statusを止める。

## Receiptと公開条件

Launcherは`validation/llama32_3b_mps_emoji_transport_v2/`へno-overwrite receiptを書く。最初の
process前に`attempt_started_receipt.json`、完走時に`execution_receipt.json`、捕捉したfailure時に
`failed_execution_receipt.json`を書く。Success receiptはstart receiptをhash固定し、failure
receiptが存在しないことを要求する。

公開証拠rootは
[`artifacts/llama32_3b_mps_emoji_transport_v2/`](../artifacts/llama32_3b_mps_emoji_transport_v2/)、
freeze manifestは
[`data/manifests/llama32_3b_mps_emoji_transport_v2.json`](../data/manifests/llama32_3b_mps_emoji_transport_v2.json)
とする。Local runには19 fileを残す。Gitのcompact bundleはrunごとに検証済み15 fileを収録し、
raw `interventions.jsonl`、`source_activations.npz`、`directions.npz`、`target_baselines.npz`を
除外する。Root manifestは除外fileのhash、byte数、rowまたはarray metadataを記録し、公開member
すべてをhash固定する。上書きはしない。

## 主張境界

正の場合に許される最も強い表現は、探索済みtarget 24件において、事前凍結した
Transformers/MPS限定のLlama 3.2 3B FP32-runtime matched-slot出力fingerprint transportを観測し、
別にcenteringしたtokenizer同型感度armを併記した、という範囲である。

正のprimary rowでも、絵文字の意味、意味family、tokenizer非依存性、独立targetによる確認、
因果局在、generation挙動、backendを切り分けた再現、model-scale効果は確立しない。V2はC1を
更新せず、因果主張を許可せず、単独でPhase I論文gateを閉じない。負またはinvalidな結果にも
同じ境界を適用する。
