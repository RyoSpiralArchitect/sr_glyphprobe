# T14-X拡張とT14-C因果実験の結果

[English](EMOJI_STEERING_T14_X_T14_C_RESULTS_V0.md) · [T14-X protocol](EMOJI_STEERING_SPECIFICITY_EXPANSION_V0.ja.md) · [T14-X解析](EMOJI_STEERING_SPECIFICITY_EXPANSION_ANALYSIS_V0.ja.md) · [T14-C protocol](EMOJI_STEERING_CAUSAL_PATH_V0.ja.md)

## 一段落でまとめると

T14-Xで見つかったのは、普遍的な「絵文字方向の強さ」ではなく、**符号までmodel・depthに依存する応答異方性のregime**だった。12個のmodel×depth JS区間はすべて0を含まなかったが、正が9、負が3だった。続くT14-Cでは、Llama 3.2 3Bのcomponentを事前固定した規則で1つ選び、新しい未使用192-target bankに対して一度だけ検定した。選ばれた`mlp_out` block 24はすべてのengineering controlを通過したが、登録済みのtreatment・necessity・sufficiency intersection-union testは棄却しなかった。これは完了した負の因果結果である。新しいtarget上にも弱いstructured-versus-null応答は残ったが、選択部位がその必要かつ十分な媒介だとは支持されなかった。

| 段階 | 固定した範囲 | 結果 |
|---|---:|---|
| T14-X収集 | base model 6 role × 後期depth 2点 | 応答559,488行、6 / 6 role完了、generation 0回 |
| T14-XA解析 | 探索family 7組を全件解析 | summary 3,060 cell、各cellでtarget bootstrap 20,000回 |
| T14-C局在化 | 候補8部位＋positive / sham control | 25,600 record、凍結済み規則で`mlp_out` block 24を選択 |
| T14-C C1 v2確認 | 未使用target 192件、12 strata | 15,360 record、因果IUTは非棄却 |

## 拡張で見えたのは、符号を持つregimeだった

X1のheadlineは、各model・depthでstructured glyph prototypeと、poolしたcovariance-matched nullを比較する。標本単位はtarget promptである。次の値はtarget単位JS差の中央値と、20,000回bootstrapによる95%区間である。

| Model | Depth | JS超過量の中央値 | 95%区間 | 符号分類 |
|---|---:|---:|:---:|---|
| Llama 3.2 3B base | 0.875 | +0.002838 | [0.001758, 0.003755] | 正 |
| Llama 3.2 3B base | 1.0 | +0.006457 | [0.003712, 0.009787] | 正 |
| OLMo 2 1B base | 0.875 | +0.006478 | [0.004045, 0.014886] | 正 |
| OLMo 2 1B base | 1.0 | +0.008591 | [0.005243, 0.013730] | 正 |
| Qwen 2.5 0.5B base | 0.875 | +0.010018 | [0.007638, 0.014669] | 正 |
| Qwen 2.5 0.5B base | 1.0 | +0.009669 | [0.005644, 0.012085] | 正 |
| Qwen 2.5 1.5B base | 0.875 | +0.001924 | [0.001399, 0.002638] | 正 |
| Qwen 2.5 1.5B base | 1.0 | -0.011136 | [-0.013932, -0.007894] | 負 |
| Qwen 2.5 3B base | 0.875 | -0.004870 | [-0.007635, -0.003734] | 負 |
| Qwen 2.5 3B base | 1.0 | -0.010316 | [-0.013234, -0.006414] | 負 |
| Qwen 2.5 7B base | 0.875 | +0.003066 | [0.002187, 0.003748] | 正 |
| Qwen 2.5 7B base | 1.0 | +0.004370 | [0.003056, 0.006184] | 正 |

Qwen系列は明らかに非単調である。0.5Bは正、1.5Bはfinal depthで符号反転、3Bは両depthで負、7Bは再び正となった。このgridから単調なscale lawを読むことはできない。KLとtotal variationも同じ9正・3負の区間分類だった一方、argmax flipは大半がmixedだった。安定して言えるのは連続的な分布応答の異方性であり、普遍的なbehavioral flipではない。

## 分解結果は、普遍的なglyph特権を認めない

JSの完全familyは不均一なままだった。

| Family | 正 | 負 | Mixed | 合計 |
|---|---:|---:|---:|---:|
| X1 structured vs covariance null | 9 | 3 | 0 | 12 |
| X2 glyph-system分解 | 51 | 15 | 6 | 72 |
| X3 prototype source-form specificity | 89 | 104 | 71 | 264 |
| X4 item source-form specificity | 43 | 64 | 25 | 132 |
| X5 final-minus-late depth | 2 | 1 | 3 | 6 |
| X6 covariance-null family感度 | 6 | 3 | 3 | 12 |
| X7 sign orientation | 7 | 2 | 3 | 12 |

因果設計に使ったLlama 3.2 3B depth 0.875では、6つのglyph systemすべてがcovariance nullに対して正だった。Atomic anchor `0.002406`、keycap `0.001110`、modifier `0.003731`、presentation `0.002654`、regional flag `0.002596`、ZWJ `0.003665`である。このcellを幅広い運用上の応答候補として扱う根拠にはなるが、glyph表記が一意に特権的だとは言えない。X3とX4のsource-form contrastは、全体では正区間より負区間が多い。ModifierとZWJにはglyph-over-nameの強い例がある一方、keycapのglyph対decomposed formは逆転しうる。

Nullの作り方と介入符号も効いている。X6とX7は一様に正ではない。そのためT14-Cでは、都合のよい側を選ばず、covariance-null family 2組と両符号を維持した。

## 因果検定は、負の結果として閉じた

T14-CはT14-X outcomeを開く前に凍結した。固定cellはLlama 3.2 3Bで、depth 0.875、magnitude 0.25の`resid_post` block 23介入を使う。局在化では公開済み32 target上で、block 24〜27の`attn_out`と`mlp_out`を比較した。凍結済みselectorは、eligibleな部位をtarget単位structured-minus-null necessity excessの中央値で順位付けし、score `0.0002628335`の`mlp_out` block 24を選んだ。

局在化のcontrolはすべて通過した。

- explicit zeroの最大JSは厳密に`0`;
- restoration errorの最大JSとlogit RMSも厳密に`0`;
- positive controlのnecessity drop中央値は`0.01016544`;
- upstream shamのnecessity drop絶対値中央値は`0`。

選択部位manifestをcommitした後にだけ、C1 v2 bankを物質化した。12個の固定stratumからなる未使用target 192件である。公開closeoutにはtarget prompt本文を保存していない。一度限りの確認では、各targetについて80個の符号付き条件にtreatment、necessity、sufficiency、restorationのpathを適用した。

| 登録済みcomponent | 点推定 | 95% target bootstrap区間 | 片側sign-flip p | 実用床 | 合格 |
|---|---:|:---:|---:|---:|---|
| Treatment | +0.00172230 | [0.00151002, 0.00190555] | 0.00001 | 0.0020 | いいえ |
| Necessity | -0.00057689 | [-0.00061168, -0.00052984] | 1.0 | 0.0005 | いいえ |
| Sufficiency | +0.00002126 | [0.00001144, 0.00003608] | 0.00001 | 0.0005 | いいえ |

Treatment contrastは正で安定しているが、事前指定した実用床に届かない。Necessityは正ではなく安定して負で、sufficiencyは正でも実用床より約1桁小さい。登録した主張はintersection-union testなので、1 componentでも失敗すれば非棄却になる。今回は3つすべてのruleが不合格である。`confirmatory_claim_authorized`は`false`のままとする。

次の部位を選ぶ、floorを下げる、model subsetを選ぶ、endpointを替える、といった救済は行わない。分散した経路、冗長な経路、あるいは抑制的なdownstream routeは将来仮説として自然になったが、このprotocolで検証した事実ではない。

## 論文gateの更新

- Phase Iのgate 4は完了した。公開freezeのもとで対象を絞った因果実験を終え、結果は負だった。
- T14-Xは広い探索的な境界地図を与えるが、独立した確認再現やscale lawではない。Gate 5は未完了である。
- T14-Cではtarget-cluster bootstrapと固定99,999回のpaired sign-flipを使ったが、論文全体の統計資格では、他の主張familyも統合する必要がある。
- 完全なraw evidence archiveと、先入観のない論文reviewはまだ未完了。英日文書の対は維持する。

次のきれいな科学的手は、同じbankでの救済ではない。まず論文のclaim tableとarchiveを仕上げる。その後future workとして進めるなら、新しい未使用bankと独立modelまたはbackendを用い、複数部位またはpath-level介入を新しいprotocolとして凍結する。

## Evidence anchor

| Evidence | Anchor |
|---|---|
| T14-X実行freeze | commit `14408a3` |
| T14-C因果freeze | commit `ff643ea`; manifest SHA-256 `9f3058c347cd1202ba12bf873b9896e919c7f8d2fde51028655c45c9c6c3a372` |
| T14-XA解析freeze | commit `143e1be`; manifest SHA-256 `7f5403246aa23779d33922d9294e3556e7a35757cd62fc8185a5681feb3de6e2` |
| 選択部位binding | commit `2d11cb6`; manifest SHA-256 `9876695b24765e94d5eb1f5f42d394aecf42724da1c98d7f732efbe40d8c2240` |
| T14-XA完全結果 | SHA-256 `cd012355867b32800a4815b20ade08d2738a5b0248418e8addd7f8283fa060a5` |
| 局在化summary | SHA-256 `dd75ec378bd420dff7bb4e566a4b574c57fbe6437c1e581bce1cd74071f8e4ca` |
| C1 v2 bank / receipt | SHA-256 `6611a9fb1720a2bc55613c8e9ee12c290577f0a610ec1e8ccf98d39a2291c7fd` / `b42f96aa12c8f9b47eb683d6c61588d8a571f74829e66f5c7823b2d84ba7d613` |
| 確認summary | SHA-256 `8e6ed50eb1afa40d98144e04ff8092ca6ba7e3d2a23ee5c103ba26cdb2f41f12` |
| 因果解析JSON | [c1_v2_result.json](../validation/emoji_steering_causal_path_v0/c1_v2_result.json), SHA-256 `3ec6fa99a4ca161a9b3f6d1a7981940b7eb2a9860fa3272e031e2f35084a9f7a` |
| 統合closeout | [t14_closeout.json](../validation/emoji_steering_causal_path_v0/t14_closeout.json) |

T14-XAの完全結果とraw run ledgerは、compact closeoutに記録したfurnace上のpathに残っている。Repository closeoutはそのhashを固定するが、未完了のarchive deposit gateそのものを置き換えるものではない。
