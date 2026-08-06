# Milestone 2 確認実験プロトコル

[English](MILESTONE2_PROTOCOL.md) · [ロードマップ](ROADMAP.ja.md) · [科学的契約](SCIENTIFIC_CONTRACT.ja.md)

プロトコルID: `glyphprobe-m2-tokenization-controls-v1`

凍結状態: Milestone 2 のモデル推論と結果確認に先立って作成した。この文書、凍結bank manifest、対照manifest、実行設定、解析コードを初めて含む公開Gitコミットを、プロトコルの凍結時点とする。凍結したv1ファイルは上書きしない。変更が必要な場合は、新しいプロトコルIDとバージョン付きファイルを作成する。

## 確認する問い

色付き図形パネルは、あらかじめ指定したGPT-2のトークン数とトークン接頭構造を揃えた固定対照パネルに比べ、targetをまたいで識別しやすい出力fingerprintを残すか。

GPT-2で「別のglyphなのにtoken列は完全に同じ」という対照は作らない。GPT-2のtoken ID列は特定のbyte列へ復号されるため、token列を完全に揃えると入力自体が同じになる。したがって、この実験で認められる結論は、指定済みのtoken count/prefix対照に対する頑健性、または非頑健性に限る。「tokenizationの影響を除いたglyph効果」とは主張しない。

## 凍結データの役割

| Bank | 役割 | 使用範囲 |
|---|---|---|
| 既存`prestage_targets`の先頭24件 | 探索用 | 対照実装、診断、CountSketch感度分析、後続の介入点探索 |
| `p2_confirmatory_targets_v1` | P2の一回限りの確認用 | 以下で定めるprimary endpointのみ。adapterのdebug、閾値調整、介入点選択には使わない |
| `c1_causal_holdout_targets_v1` | 将来のC1確認用 | 介入方法と判定規則を凍結した後の最終因果試験に限る |
| 既存`source_wrappers` | P2 primaryのsource手続き | 公開済みsource手続きに条件づけたtarget一般化の確認 |
| `milestone2_independent_source_wrappers_v1` | source頑健性 | 独立した頑健性arm。target clusterと合算して標本数を水増ししない |

2つのholdout bankは、それぞれ48件で構成する。`continuation`、`factual`、`reasoning`、`procedural`、`classification`、`planning`の6群に各8件を割り当てた。正確なhashと禁止事項は`data/manifests/milestone2_frozen_banks_v1.json`に記録する。

## 固定panelと診断arm

primaryの色付き図形パネルは10条件からなる。raw token列の先頭は、9条件が`[8582, 253]`、`blue_circle`だけが`[8582, 242]`である。10 glyphはいずれもraw token数が3である。

primaryのmatched-control familyには、互いに素な10-symbol panelを3組置く。

- `m2_null_prefix_9x253_1x242_a`
- `m2_null_prefix_9x253_1x242_b`
- `m2_null_prefix_9x253_1x242_c`

各panelは、色付き図形パネルと同じ9:1のprefix strata、同じ10条件、各symbol 3 raw tokensを保ち、wrapper tokenizationの固定検査を通す。参照glyphと中立対照を除くと、主要prefixに該当する非色付きsymbolは26個しかない。一方、互いに重ならない3 panelには27枠が必要である。そのためpanel Cには、参照panelに含まれない赤い四角`🟥`を、事前指定した意味的に近い対照として1個だけ含める。残る29条件は非色付きsymbolである。この保守的な例外は結果を見る前に記録し、結果確認後の差し替えには使わない。

候補の生成・除外・割り当てに使えるのは、tokenizer出力、Unicode metadata、wrapper構造だけである。activation、logit、生成文、既存セルの効果量は選定に使わない。

次の2 panelはsecondaryな診断armとする。

- `m2_suffix_matched_middle_236`: 各primary条件の先頭tokenと末尾tokenを保ち、中間tokenだけを置き換える。
- `m2_colored_shapes_prefix_10x253`: 青のpairを黄のpairに置き換え、10条件すべてのprefixを`[8582, 253]`へ揃える。

この2つの診断armを、primary endpointの3-panel matched-null familyの代わりに使ってはならない。

## 固定するモデル条件

- model: `openai-community/gpt2`
- revision: `607a30d783dfa663caf39e06633721c8d4cfcd7e`
- backend: 資格確認済みのMLX/MLX-LM経路
- dtype: FP32
- 介入点: full-sequence `resid_post`
- primary layer: 2、4
- primary strength: target activation RMSの0.05
- direction seed: 101、211、307。target内の反復推定として扱う
- fingerprint: seed 8675309で固定した96次元CountSketch

一回限りのprimary runは、`configs/m2_p2_primary_mlx.yaml`と3つの`configs/m2_p2_matched_null_{a,b,c}_mlx.yaml`で固定する。実行するのはlayer 2/4、strength 0.05、zero-hook検査だけである。別報告とするsource頑健性armは、対応する4つの`*_independent_source_mlx.yaml`で固定する。P2 bank上でsecondary cellを暗黙の救済探索に変えないため、実行matrixをこの範囲に限定する。

Layer 7/9、strength 0.025/0.10、glyph別解析、2つの診断panel、random control、generic-glyph方向は、探索またはsecondaryにとどめる。一回限りのP2 configでは実行せず、primary familyが不通過でも、これらを根拠に救済しない。

2つのprimary layerは、公開済みの探索mapから選んだ。P2 bankを選択に使っていないため、この選定は許容する。ただし、heterogeneityは裏付けではなく警告である。探索結果では、layer 2のseed 307とlayer 4のseed 101が、全strengthで負だった。

## Target単位のprimary endpoint

固定したlayer/strengthについて、panel `p`、condition `c`、target `t`、direction seed `s`の単位長96次元fingerprintを`f[p,c,t,s]`とする。

Target group `g`ごとに、そのgroupを除外したtargetだけでcondition prototypeを作る。

```text
q[p,c,-g,s] = unit_mean({f[p,c,u,s] : group(u) != g})
```

Target `t`のleave-one-group-out識別scoreは次のとおり。

```text
S[p,t,s] = mean_c cosine(f[p,c,t,s], q[p,c,-group(t),s])
           - mean_{c != d} cosine(f[p,c,t,s], q[p,d,-group(t),s])
```

Direction seedはtarget内で平均する。標本数には数えない。

```text
S[p,t] = mean_s S[p,t,s]
```

Primaryの調整済みtarget効果を次のように定める。

```text
D[t] = S[colored_shapes,t]
       - median_b S[matched_null_b,t],  b in {a,b,c}
```

Primary layerごとのtarget clusterは48件である。Glyph、direction seed、split反復、null panel、CountSketch次元を独立標本として数えない。

## 確認的推論

- estimand: P2 target 48件における`D[t]`の平均
- 不確実性: 6つの固定group内で各8 targetを復元抽出する、20,000回のpercentile cluster bootstrap
- bootstrap seed: 20260806
- 最小限意味のある超過量（`delta`）: fingerprint separation 0.06。matched-controlの結果を見る前に、公開済み探索中央値のおよそ10%として定めた
- primary family: strength 0.05のlayer 2とlayer 4
- 多重性補正: 2仮説に対するHolm法、family-wise alpha 0.05
- permutation screen: `D[t] - delta`をtarget単位で符号反転する100,000回のpaired draw、seed 20260807。区間推定に対するsecondaryな検査とする

Primary layerを**指定済みmatched controlsに対して頑健**と判定するには、95% bootstrap CIの下限が`delta`を上回り、片側permutation p値がHolm補正後も0.05未満でなければならない。

95% CI全体が`[-delta, delta]`内に収まった場合に限り、**matched-null ensembleと実質同等**と判定する。それ以外は**未解決**とする。棄却できなかった結果を、「tokenizationが探索結果の原因だった」という証明に読み替えない。

36セルの記述表には、primary値、matched-null中央値、加法差、null-panel内percentile、符号変化、低次元CountSketch感度を記録する。36セルは相関しているため、全セルをまとめたp値や独立標本としての解釈は行わない。

## 候補選定とholdoutのgate

P2の判定規則を通過したprimary layerだけを、限定的な因果局在化へ進める。凍結済みの独立wrapper bankを使ったsource頑健性は、primaryと分けて報告する。同じ固定解析で調整済み効果の符号を保ち、実質同等域をまたがない場合にsource-robustとする。Source wrapperの反復も、標本数には加えない。

`resid_pre`、`attn_out`、`mlp_out`は、モデル系列ごとのparity確認後、既存24 targetsで探索できる。C1の結果は参照しない。C1 bankを開く前に、介入点、候補layer、strength、patch/ablation手続き、negative controls、endpoint、多重性familyを新しいC1プロトコルで凍結する。

## CountSketchとbackendの感度分析

96次元fingerprintをprimaryとする。同じhash seedなら、保存済み96 bucketをfoldして再正規化することで、48、32、24次元を正確に再構成できる。これらはsecondaryな感度分析であり、標本数を増やすものではない。別のCountSketch seed、または96を割り切れない次元には、full-vocabulary logit deltaか、新たなforward passが必要になる。

TransformerLensでの再現は、独立したbackend実装の確認であり、別model familyによる再現ではない。固定セルについて、token ID、BOS方針、baseline logit、activation、zero hook、non-zero interventionのparityを先に通す。Adapterのdebugにconfirmatory targetsを使わない。

## 停止規則と報告

P2 bankを開くのは、プロトコル、manifest、config、解析実装がすべてtestを通過した後の一度だけとする。Primary、negative、heterogeneous、equivalent、unresolvedの結果をまとめて公開する。Protocol v1では、結果を確認した後にsymbol、target、source wrapper、layer、strength、CountSketch設定、endpointを差し替えない。

凍結した実験とevidence archiveの同定可能性・再現可能性を保てるなら、明瞭な負の結果やmixed resultもMilestone 2の完了として扱う。
