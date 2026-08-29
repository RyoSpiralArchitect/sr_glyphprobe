# 絵文字steering特異性データ収穫 v0 — T13-EHプロトコル

[English](EMOJI_STEERING_SPECIFICITY_HARVEST_V0.md) · [T13の問いの地図](EMOJI_STEERING_SPECIFICITY_ATLAS_V0.ja.md) · [T12結果](GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.ja.md) · [ロードマップ](ROADMAP.ja.md)

プロトコルID：`glyphprobe-emoji-steering-specificity-harvest-v0`

Freeze時点の状態：**静的protocol。manifest作成前のT13-EH model forwardは0件**。
実行後の進捗は、この文書ではなくhashで拘束したrole receiptに記録する。

T13-EHで決めるのは、研究結果ではなく作業順である。GPUが必要なテンソルを先に収集し、解析・可視化・多重性の設計・論文執筆はCPUまたはMPSで後から行う。主要仮説、実用上の閾値、確認的な合否判定は置かない。

## なぜ、執筆より先に収集するのか

炉は、GlyphProbeと無関係な事情でも長時間使えなくなりうる。次の研究で最も移しにくい工程はmodel forwardであり、幾何解析、matching、resampling、作図、執筆の大半は、あとからどちらのMacでも進められる。いま一枚の再利用可能な応答テンソルを取っておけば、急いで図を一枚選ぶよりも、後の選択肢を広く残せる。

炉の空き具合に応じて変えてよいのは、queue順、batch size、shardの切れ目だけである。項目母集団、モデル群、source form、wrapper、target、深度、符号、強度、endpoint、停止規則は変えない。queueの途中で科学的な結果も読まない。

## T11・T12との関係

母集団は、T11で使った192項目のdepth populationに固定する。全項目がT11ですでにforward済みであり、まだ使っていないpresentation、modifier、keycapのreserveは消費しない。T12で開いたZWJ・regional reserveの結果を、T13-EHの項目やendpoint選択にも使わない。

T12を再解釈する実験でもない。登録したT12の2仮説は、未確認のままである。T13-EHは、T12が残した広い問いへ戻るための、新しい探索的source-form／介入データ収穫である。

## 固定する母集団と公開target

192項目は、T11で凍結したdepth index順に並べる。

| glyph system | 項目数 |
|---|---:|
| atomic anchor | 24 |
| presentation sequence | 24 |
| modifier sequence | 40 |
| ZWJ sequence | 56 |
| regional flag | 40 |
| keycap | 8 |

source formは、T11で定めたものをすべて残す。glyph、Unicode公式名、決定論的component名、codepoint literal、決定論的decomposed formの5種である。atomic anchorは3種、ほかのsystemは5種となり、item-formは合計912行になる。

targetには、公開済みの`prestage_targets.jsonl`全32行をファイル順で使う。P2とretired C1 v1は、開かず、tokenizeせず、forwardもscoreもしない。generationも行わない。

## 固定するsource bank

結果を見る前に、公開済みwrapperから次の4種を選ぶ。

- `w01_mark_anchor`
- `w04_token_state`
- `w10_sequence_continuation`
- `w15_observation_inference`

各item form・各深度で、source付きpromptと同じbare wrapperの差を取る。読み出すのは、wrapper末尾tokenにおけるdecoder blockの生出力である。4本のwrapper deltaを等しく平均し、mean directionとする。正規化深度は`[0.125, 0.25, 0.375, 0.50, 0.625, 0.75, 0.875, 1.0]`の8点。block indexは`max(0, floor(fraction × num_layers) - 1)`で決める。

T10〜T12と同じ9つのmodel/tokenizer cellすべてで、source bankと32 targetのbaselineを取る。1モデルあたりの保存量は次のとおり。

- wrapper deltaの全FP32ベクトル：29,184本
- mean directionの全FP32ベクトル：7,296本
- target activationの全FP32ベクトル：256本
- baseline next-token logitsの全FP32ベクトル：32本

9モデルでは、activation vectorが330,624本になる。入力系列は合計33,156本。計算上のbatchは機種ごとに変えるが、系列母集団は変えない。

## 代表3モデルの固定介入pilot

結果を見る前に、小型base、3B級base、7B級baseを1つずつ選ぶ。

1. `qwen25_0p5b_base_bf16`
2. `llama32_3b_base_bf16`
3. `qwen25_7b_base_bf16`

介入位置は、target末尾tokenの指定decoder block生出力。directionをunit RMSへ正規化し、`符号付き強度 × target activation RMS`を掛けて加える。

各モデルで、次の4 gridを欠けなく回す。

| grid | 固定範囲 | 行数／model |
|---|---|---:|
| item source form | glyph／name／decomposedの552方向 × 32 target × 2符号。深度0.50、強度0.25 | 35,328 |
| system-form prototype | itemごとにunit RMS化した28 prototype × 8深度 × 3強度 × 2符号 × 32 target | 43,008 |
| random null | 決定論的な等方random 64本 × 8深度 × 3強度 × 32 target | 49,152 |
| zero hook | 8深度 × 32 target。完全なno-opを必須とする | 256 |
| **合計** | 固定pilot全体 | **127,744** |

3モデルを合わせた介入応答は383,232行になる。介入batchごとにzero vectorのguard行を同梱し、同じtarget・batch形状・数値経路を通ったbaselineと比較する。

## 保存する応答面

各行には、条件ID、itemまたはprototypeの由来、source form、system、target、深度、block、強度、符号を記録する。測るのは、KL divergence、Jensen–Shannon divergence、total variation、介入前後のentropy、logit delta RMS、top-1変化である。

何十万本ものfull-vocabulary logitsを毎回保存せず、それでも後の解析余地を残すため、各行に次も保存する。

- 正方向のlogit delta上位64 token
- 負方向のlogit delta上位64 token
- 完全なlogit deltaから作る決定論的256次元CountSketch

baseline logitsは、target・modelごとに一度だけ完全保存する。raw source／response arrayは炉に置き、hashで拘束する。GitにもSpiralShareにも載せない。

## 再開と競合の扱い

source収集は、1モデルにつき16項目×12 shardへ分ける。item介入も同じ12 shard、prototypeはglyph system単位、random controlは深度単位で区切る。完了shardは不変とし、検証を通してから次へ進む。

途中のstaging directoryが残った場合は、人が内容を確認するまで再利用も削除もしない。model load前と各shard開始前には、ほかのGPU processを確認する。競合が現れたらyield receiptを書き、次のshardへ入らずexit code 75で終了する。他者のworkloadをpause、kill、変更することはない。

## あとでCPU／MPSへ回す仕事

収集工程ではoutcome analysisを行わない。GPU queueが閉じたあと、保存テンソルから次を調べられる。

- tokenizer signatureを揃えたsource-form比較
- item・system・target・depth・model・dose・signのheterogeneity
- 正負介入のantisymmetryと非線形dose診断
- target entropy／top-two marginへの感度
- top deltaとCountSketchを使ったsemantic probe探索
- 補遺図、またはFuture Workへ送る候補の選定

将来T13-Cを行うなら、新しい未使用target bankと新しいfreezeが必要になる。T13-EHの観測値をT13-Cの検定統計へ混ぜてはならない。

## 主張境界

T13-EHは、探索用データを先に収集する実験である。見栄えのよいpatternや複数モデルで揃ったpatternが見つかっても、それだけでは、絵文字意味、理解、絵文字固有の特異性、因果機構、behavioral steering、tokenizer independence、scale law、instruction-tuning効果、architecture／model populationへの一般化、独立再現を示せない。null、heterogeneous、failed shardも、同じ境界のまま保存する。
