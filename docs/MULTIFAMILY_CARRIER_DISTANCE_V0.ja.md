# 多ファミリー反復キャリア距離 v0

[English](MULTIFAMILY_CARRIER_DISTANCE_V0.md) · [T4結果](MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.ja.md) · [研究ロードマップ](ROADMAP.ja.md)

プロトコルID: `glyphprobe-multifamily-carrier-distance-v0`

## 状態と限定した問い

これは、前向きに固定する探索的・観察的な反証実験です。英日文書、
設定、実行・解析コード、テスト、工学的事前確認、チェックサム付き
manifestを初めて公開するcommitを、実行可能な凍結点とします。この
commitより前に、本プロトコルのactivation結果を見てはいけません。

T4では、グリフの1 token後に置いた共通token上で、OLMoにmatched-slot
幾何が残り、Gemmaでは残りませんでした。したがって「現在tokenが元の
slot tokenであるときだけ現れる」という狭い説明は退けられます。一方、
直近にだけ残る局所的な痕跡なのか、より長い文脈伝播なのかは未分離です。

本プロトコルでは、入力全文と現在のキャリアtokenの種類を固定したまま、
グリフから1、2、4、8 token後のresidual streamを読みます。距離1での
再現と、事前に固定した正の対数距離減衰contrastが両立するかを調べます。
絵文字の意味や因果機構を検定する実験ではありません。

## 固定パネル、キャリア、読出し位置

T3/T4と同じパネルをそのまま使います。sky、food、animals、transport、
socialの5ファミリーに、Unicode上の相対位置を揃えた10 slotずつ、計50
グリフです。グリフ、ファミリー、slotの追加・削除・並べ替えは禁止です。

各グリフの後ろに、次の8 tokenキャリアを付けます。

| キャリア | 末尾に加える正確な文字列 | Gemma token | Llama token | OLMo token |
|---|---|---:|---:|---:|
| `article_a` | `" a"`を8回 | 476 | 264 | 264 |
| `pipe` | `" |"`を8回 | 1420 | 765 | 765 |

モデルforwardを一度も行わないtokenizer事前確認により、全50項目・3モデルで
次を確認しました。

1. 文脈付きtoken化でも、元グリフのtoken列が完全な接頭列として残る。
2. その後ろに、同一のキャリアtokenが正確に8個続く。
3. 結合後も50入力がすべて区別される。
4. decodeすると、元グリフとキャリア文字列へ正確に戻る。

読出し位置は `raw_token_count + distance - 1`、距離は
`[1, 2, 4, 8]` に固定します。どの距離でも8 tokenすべてを含む同じ入力を
forwardし、変えるのはcapture位置だけです。距離によって入力長や現在tokenが
変わることは避けられますが、グリフ・キャリアごとに4回の独立forwardが必要です。

同一tokenの反復自体が、反復に固有のダイナミクスを生む可能性は残ります。
2種類のキャリアは単一tokenへの依存を弱めますが、この限界を解消しません。

## 固定する3つのMLXモデルセル

| 役割 | ノード | 元パネルのtoken化 | 精度 |
|---|---|---|---|
| `gemma2_2b_4bit` | mac2 | 50個の相異なるatomic glyph token | MLX 4-bit |
| `llama32_3b_bf16` | mac2 | 47個は3 token、3個は固定した2 token列 | MLX BF16 |
| `olmo3_7b_bf16` | mac1 | 共通接頭辞 + family + slotの完全因数分解 | MLX BF16 |

Llama 3.2 3Bは、より大きいモデルへの転送セルとして本実行より前に選ばれて
います。3グリフではfamily/slotの名目的な組がmergeされるため、元token列
全体をSHA-256で固定します。LlamaとOLMoでは2種類のキャリアtoken IDが一致
しますが、元グリフのtoken化は完全には一致しません。tokenizer同等性は主張
しません。

各モデルで、`resid_post`を固定した深さ比率
`[0, 0.25, 0.5, 0.75, 1]`から取得します。forward回数は1モデルあたり
`50 × 2 × 4 = 400`、合計1,200回です。生成、介入、保護targetへのアクセス、
furnaceでの計算は行いません。

LlamaのMLX Stage-A parity gateは、引き続き未通過です。したがって、これは
native MLXによる観察セルであり、backend同等性を備えた測定ではありません。

## 唯一の主要判断

各キャリア・距離・深さでactivationをfamily × matched slotに並べ、各family
平均を除いた後のslot比率を

\[
S_{c,d,\ell} = \frac{SS_{\mathrm{slot}}}
{SS_{\mathrm{slot}}+SS_{\mathrm{interaction}}}
\]

とします。主要判断は、次の2条件を両方要求するintersection-union testです。

1. **距離1での再現:** 2キャリア・5深さにおける
   \(S_{c,1,\ell}\) の等重み平均。
2. **減衰contrast:** 距離 `[1, 2, 4, 8]` に固定重み
   `[0.375, 0.125, -0.125, -0.375]` を掛け、キャリア・深さについて
   等重み平均した値。

このcontrastは `log2(distance)` に対する負の線形傾きを、絶対重みの和が1に
なるよう尺度化したものです。正の値は平均的な減衰を支持しますが、隣接する
全距離で単調に低下することも、距離8で消失することも要求しません。

nullでは、skyを参照familyとして固定し、それ以外の各family内で10 slotの
ラベルを独立に並べ替えます。PCG64の各drawは、全40個の
キャリア × 距離 × 深さセルで同じ4つの並べ替えを共有します。seedは
`20260830`、draw数は19,999に固定し、各片側p値を

```text
p = (1 + count(T_randomized >= T_observed)) / 20,000
```

で求めます。モデルごとのintersection-union p値は2成分の大きい方です。
したがって、両成分が小さくなければ棄却できません。3モデルのp値を1つの
Holm familyとして、familywise alpha 0.05で補正します。キャリア、距離、
深さ、距離8 tail、モデル間の大きさ比較を、この判断の代わりにはできません。

## 固定した分岐と主張境界

3モデルすべて、Llama/OLMoの組、各単独モデル、その他の2モデル組、棄却なしを
事前分岐として用意します。どの分岐でも完全な距離profileを残します。T4は
設計動機と記述的参照として固定しますが、本検定にはpoolしません。

あるモデルが棄却した場合に言えるのは、固定したパネル、キャリア、深さ、MLX
セルにおいて、距離1のmatched-slot再現と、固定した正の減衰contrastが共存した
ということだけです。単調減衰、消失、意味表現、因果的伝播、行動steering、
tokenizer同等性、architecture効果、scale効果、backend parity、確認的再現、
Phase I gate通過は示しません。

本実験は、低コストな観察的識別です。tokenization-matched confirmatory controlsや、
held-outな因果実験の代わりにはなりません。
