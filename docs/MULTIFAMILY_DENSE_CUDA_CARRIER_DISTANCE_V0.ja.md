# Multifamily dense CUDA carrier-distance v0

[English](MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0.md) · [T5結果](MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.ja.md) · [ロードマップ](ROADMAP.ja.md)

状態: **T6 model forward 0のprospective freeze**。この文書、実行code、config、test、
preflight、model manifest、checksum manifestを1つの公開commitで結び付けた時点で、
freezeが完了する。

## 問い

T5では、LlamaとOLMoの距離1成分にrecurrenceが見られた一方、距離1のrecurrenceと
固定した正のcarrier-distance減衰contrastを同時に要求する主判定を通過したmodelは
なかった。T6では、炉に完全なartifactがある4つのdense Transformers/CUDA cellで、
この観測endpoint全体が再現するかを調べる。

Model rosterはT5の結果を見た後に選んだ。そのためT6がprospectiveなのは、まだ見ていない
T6自身の結果に対してだけである。T5の独立確認ではなく、選択した2B・4B・7B・12Bの
4 cellをscale推論へ変えるものでもない。

## 固定model roster

| Role | 固定artifact | Parameter数 | Layer × width | 生のglyph token | Model出力語彙 |
|---|---|---:|---:|---|---:|
| `gemma2_2b_it` | `google/gemma-2-2b-it@299a856…` | 2,614,341,888 | 26 × 2,304 | 50件すべて1 token | 256,000 |
| `gemma3_4b_it` | `google/gemma-3-4b-it@093f9f3…` | 4,300,079,472 | 34 × 2,560 | 49件が1、1件が4 token | 262,208 |
| `mistral7b_instruct_v03` | `mistralai/Mistral-7B-Instruct-v0.3@c170c70…` | 7,248,023,552 | 32 × 4,096 | 49件が5、1件が2 token | 32,768 |
| `gemma3_12b_it` | `google/gemma-3-12b-it@96b6f1e…` | 12,187,325,040 | 48 × 3,840 | 49件が1、1件が4 token | 262,208 |

各snapshotはローカルに完備され、全ファイルmanifestで固定する。Llama 3 8B base、Llama
3 8B Instruct、Gemma 2 2B baseはcacheにrefしかなく、T6 activationを見る前に除外した。
選んだ4モデルはすべてinstruction-tunedだが、chat templateもspecial tokenも加えない。

Gemma 3の4Bと12Bは、観測したtokenizer rosterが完全に同じである。記述的なpair比較には
使えるが、1組だけをscale標本とは扱わない。

## Model forward 0のtokenization・artifact preflight

Engineering preflightでは、model forward、介入、生成、protected-target readをすべて0に
保ち、次を固定した。

- 生の50 itemすべてのtoken列を、順序付きSHA-256で固定
- tokenizerごとのtoken数histogramと共通prefix列
- `" a"`と`" |"`を8回反復するcarrierのtoken identity
- raw prefixの完全保存、結合列SHA-256、50/50のdecode round trip
- model revision、全artifact manifest、indexから得たparameter数、architecture次元、
  BF16実行契約

公開preflightには、端末固有のmodel pathを含めない。

## 固定inputとcapture

T6は公開済み5 family × 10 slot panelを再利用する。各glyphとcarrierについて、
raw-glyph-plus-eight-carrier-tokenの完全な入力を、距離1、2、4、8ごとに独立forwardする。
4つの読み出しで入力全体と現在位置のcarrier-token identityは変えず、capture位置だけを
変える。

`resid_post`は、fraction `[0, .25, .5, .75, 1]`を
`min(num_layers - 1, floor(fraction * num_layers))`で解決した5深度から取得する。
Gemma 3では固定した`model.language_model.layers`、他のcellでは`model.layers`を使う。

1 modelあたり400 forward・2,000 vector、4 model合計で1,600 forward・8,000 vectorで
ある。Activation介入、生成、behavior scoring、protected target accessは行わない。

## 主endpointと多重性

Carrier・distance・depthごとにvectorをfamily × matched slotへ並べ、family平均を引いた後、

`SS_slot / (SS_slot + SS_interaction)`

を計算する。Modelごとに、

1. criterion Aは、両carrier × 5深度を等重み平均した距離1の値
2. criterion Bは、距離 `[1, 2, 4, 8]`へ重み
   `[0.375, 0.125, -0.125, -0.375]`を与えた等重みlog-distance contrast
3. model-level IUT p値は`max(p_A, p_B)`

とする。

Nullでは、基準family以外の4 family内でslot labelを独立に置換し、同じdrawをcarrier、
distance、depthへ同期する。PCG64 seed `20260831`で19,999 drawを行う。4つの
model-level IUT p値を1つのHolm familyとしてFWER 0.05で管理する。判定権限を持つのは、
この4つの補正済み判定だけである。

Carrier、distance、depth、tail、Gemma pair、timing、T5比較はすべて副次結果であり、
失敗したmodel-level conjunctionと差し替えない。

## 登録する分岐

- 4つのdense cellすべてが通過
- Gemma 3の4B・12B pairだけが通過
- Gemma 3 12Bだけが通過
- 上記以外の非空集合が通過
- dense cellが1つも通過しない

どの分岐でも4 modelと160 profile rowをすべて残す。失敗cellは差し替えず、都合の良い
carrier、distance、depth、model pairを結果確認後に主判定へ格上げしない。

## 運用上の開始gate

最初のT6 model load直前に`spiral status`を再確認し、競合するcompute processがないことを
実測する。さらに、新しい`resource:furnace`通知が、対象となるsubscribe済みsessionの
自然なreceiver-owned task lifecycleでsurfaceしていなければならない。Canonical publish、
watcher到着、OS popupだけでは後者を満たさない。Synthetic boundary probe、hook trustの
bypass、process interruption、自作のacceptanceは使わない。

どちらかが欠ける間もtokenizer・artifact preflightは進められるが、T6 model loadとforwardは
0のままにする。

## Runtimeと実行

固定実行cellは、PyTorch `2.13.0+cu132`、Transformers `5.15.0`、NVIDIA GeForce RTX
5090上のBF16 CUDA、local-only artifact loadである。各modelを別processで実行し、前の
modelを解放してから次をloadする。

公開freeze commitを転送してauditした後、role-bound commandは次の形になる。

```bash
python scripts/multifamily_dense_cuda_carrier_distance_v0.py audit-freeze
python scripts/multifamily_dense_cuda_carrier_distance_v0.py tokenizer-preflight \
  --model-label <role> --model-path <local-snapshot>
python scripts/multifamily_dense_cuda_carrier_distance_v0.py run \
  --model-label <role> --model-path <local-snapshot> --output <new-output-dir>
```

4つのsealed runは、固定したrole順でのみ解析する。Activation array、全observation、
scrub済みruntime/model receipt、bundleごとのSHA-256 ledger、160件の副次profile row、
joint analysis receiptを残す。

## 主張境界

T6から報告できるのは、事前指定した4つのmodel-level IUTのうち、どれがHolm補正後に
棄却されたかまでである。意味、因果機構、生成behavior、tokenizerの同等性や因果性、
単調減衰、消失、持続時間、永続的memory、base/instruct同等性、backend parity、node・
precision効果、model-scale効果、cross-modelの大きさ順位、確認結果、Phase I paper gateの
完了は示さない。
