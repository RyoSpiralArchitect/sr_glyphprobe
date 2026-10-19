# T22 CPU：露出済み8項目の語彙比較

[English](T22_CPU_LEXICAL_CANARY_V0.md) | [完了済み実装検証](T22_CPU_ENGINEERING_V0.ja.md)

状態：実装と取得前の仕様。8項目の実装検証は完了しているが、この仕様の作成時には、
その語彙スコアを調べていない。露出済み8項目の記述的比較とし、確認実験・効能screen・
384項目探索の代用とはしない。この8項目の効果の符号で大規模探索を選択・中止・再調整しない。
過去のT19/T20/T21の証拠とソースは変更しない。

## 固定入力と追加取得

取得SHA-256が `27c9e58535a872861a87c22d7b82dce7f9e54952bc229511b7231a9693dca901`
の `runs/t22_cpu_canary_v0/` だけを再利用する。
8項目について、block 21のcodepoint reset、distance 8、pipe/article-a carrier、
事前固定のtoken数を合わせた2 donor、glyph/同数suffix位置、block 22〜27の
K/V/KV/reference操作を維持する。元の16行extension batchと、各行の同一slot neutral readoutを保持する。

固定された元の128 source gallery全項目と8 targetのalias-label token列を取得する。
同じ固定9ファイルの3Bモデル、Torch 2.13.0+cpu、Transformers 5.15.0、BF16、
eager attention、CPU 4 threads・interop 1 threadを使う。
padding・cache・量子化・tokenizer・remote codeは使わない。各forwardはbatch size 1。
T21のdistance-8 alias readoutと同じ、final norm後の最後のcarrier tokenを読む。
各targetのalias取得前に、両carrierで保存済みstock glyphの全hidden stateとの完全一致を要求する。
alias 272回とstock検査16回の合計288 forwardで、新規介入forwardは不要。
ターゲットbankの読み込みや走査はしない。

ソースに結び付けた合成検証が成功してから、`prepare`で入力・source/test/docsのhash・
runtime・実装監査・指標の定義を凍結する。完了済み実装検証の親runに独立監査を要求し、
モデルmanifest全体を取得前後に検証する。2 carrier分のaliasを行ごとのhash付きreceiptと保存する。
再開できるのは同一仕様の未完了取得のみで、完了済み取得は変更しない。
ソースやstock再現の不一致があれば、科学的な解釈の前に停止する。

## スコア算出前に固定する指標と比較

float64でL2正規化し、各readout batchに対して129列を一度に行列積で評価する。
列順は正解alias、その後に元の128 source aliasを元の順番で並べる。
同点はT21と同じく正解優先。状態を先に平均せず、activeと同一slotのneutralを別々に評価する。
全cosine scoreと以下を保存する。

- 正解aliasのcosine、最強の競合語のcosineと固定source index。
- margin＝正解cosine−最強競合cosine。
- 正解と対応donorのcosine margin、正解rank、正解優先のtop-1。

各指標は、最初に元の各行で `E = active - neutral` を計算する。
操作Xの位置調整済みdecrementは、targetごとに
`Delta_X = mean_carrier,donor(E_suffix,X - E_glyph,X)` とする。
marginのDeltaが正なら、glyph置換の方がsuffix置換よりmarginを大きく下げたことを示す。
glyphの絶対decrement `-mean(E_glyph,X)` も残す。
reference・K・V・KVを並べ、記述的な相互作用 `Delta_KV - Delta_K - Delta_V` を報告する。
marginのDeltaを、正解cosineのDelta−最強競合cosineのDeltaへ厳密に分解する。
比率を機構の寄与百分率と解釈しない。Reference操作のmargin効果は厳密にゼロを要求する。

8項目すべての値・平均・中央値・標本SD・範囲を報告する。集計単位は項目であり、
2 carrierと2 donorから32項目を作らない。母集団の信頼区間、p値、判定閾値、
勝者となる操作は宣言しない。Carrier・donor別の比較と全512行のactive/neutralスコアを保存し、
異なる方向の変化が平均で隠れないようにする。

実装検証のlayer/head別attention全配列はhashに結び付けて保持する。
activeとneutralのweight L1差と、glyph/suffix attention massの変化をblockごとに要約する。
V/referenceの各layerでのlocal baselineとの一致は、neutral runとの一致と分けて検査する。
Vはlocal weightを変えないが、後のquery変化で下流のroutingは変わり得る。
Kを純粋なrouting、Vを純粋な意味とはしない。Codepoint gallery指標、restoration、生成挙動、
絵文字特異性、過去GPUとの一致は今回の取得範囲外で、ここでは未測定とする。

## コマンド

`/workspace/sr_glyphprobe` から、未使用の出力名で実行する。

```bash
.venv/bin/python scripts/t22_cpu_lexical_canary_v0.py validate \
  --output validation/t22_cpu_lexical_canary_v0/synthetic_validation.json
.venv/bin/python scripts/t22_cpu_lexical_canary_v0.py prepare \
  --canary runs/t22_cpu_canary_v0 \
  --validation validation/t22_cpu_lexical_canary_v0/synthetic_validation.json \
  --output runs/t22_cpu_lexical_canary_v0
.venv/bin/python -u scripts/t22_cpu_lexical_canary_v0.py run \
  --model-path /workspace/models/llama32_3b_bf16_t21 \
  --output runs/t22_cpu_lexical_canary_v0
.venv/bin/python scripts/t22_cpu_lexical_canary_v0.py analyze \
  --acquisition runs/t22_cpu_lexical_canary_v0 \
  --output runs/t22_cpu_lexical_analysis_v0
```

中断し、取得processが動いていないと確認できた場合、同じ`run`に`--resume`を付ける。
再開のため凍結ソースを編集しない。修理には新versionと証拠の互換性の明示が必要。
解析はraw score・比較値、CSV、attention診断、結果receipt、生成reportを出力する。
実測結果は、このソースに結び付けたスコア算出前仕様を変更せず、別に記録する。
