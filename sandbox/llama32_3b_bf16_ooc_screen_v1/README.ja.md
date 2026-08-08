# Llama-3.2-3B bf16 — 契約外の絵文字 fingerprint スクリーン (v1)

[English](README.md) · [科学的契約](../../docs/SCIENTIFIC_CONTRACT.ja.md) · [封印済み v2 プロトコル](../../docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.ja.md) · [Holdout status](../../docs/HOLDOUT_STATUS.ja.md)

> ## ⚠️ 契約外（OUT OF CONTRACT）— これは封印済み v2 実験ではない
> このディレクトリの内容はすべて**探索的・契約外**の実行である。意図的に
> `sandbox/` に隔離しており、凍結された科学的記録の一部では**ない**。
> `artifacts/`・`validation/`・`data/manifests/`・封印済み v2 の receipts には
> 一切触れず、`glyphprobe-e2-llama32-3b-mps-emoji-transport-v2` を更新・確認・
> 弱化・再解釈も**しない**。

## これは何か

GlyphProbe の**内部介入ハーネス**を、非量子化の本物の **bf16 Llama-3.2-3B** に対して
`transformers` バックエンド・Apple MPS・**FP32** で回した、スケールアップ版の探索実行。
バックエンドと重みは封印済み v2 セルと同一。目的は「本物のモデルを自前ツールで
end-to-end に動かすところを見る」ことと、pre-causal な活性化スクリーンを得ることだけ。

- Panel: `colored_shapes`（10 glyph、color×shape の factor 構造あり）
- pre-stage targets 24 · source wrappers 16 · seeds 3 · strengths 3
- 層 `[5, 11]`（v2 と同じ深さを契約外で使用）
- 介入/観測レコード 7,104 件・エラー 0・M4（MPS/FP32）で約27分

## これは何ではないか

- 封印済み v2 実験**ではない**し、その再現でも**ない**（*環境* を参照）。
- 因果・意味の主張では**ない**。ハーネス自身が `pre-causal-activation-screen`・
  `Causal claim authorized: False` と刻む。安定した分離はより鋭い因果検定を
  正当化しうるが、機構や「絵文字の意味」を同定するものではない。
- トークン化統制**されていない**：source wrapper が glyph 間でトークン長を揃えて
  いない（`wrapper_tokenization_control` は HOLD）ため、トークン化は未解決の交絡。
- 正規 provenance では**ない**：凍結外のライブラリ版＋`orjson` 代替で実行したため、
  ここの receipt ハッシュは正規 GlyphProbe 実行と比較不可。

## 結果サマリ（`results/report.md`）

Readiness gate：**10 / 11 PASS**（HOLD は `wrapper_tokenization_control` のみ＝
wrapper/panel データの性質で、knob では直せない）。

| 診断 | 値 |
|---|---|
| source-direction 複製安定性 | 0.9353 |
| zero-hook no-op（logit & 活性化 Δ RMS） | 厳密に 0.0 |
| scalar RMS 比一致誤差 | ~1e-17 |
| KL dose 単調性 | 1.000 |
| sign-flip 反対称性 | 0.9947 |
| cross-seed fingerprint 安定性 | 0.9952 |
| within-target label-permutation p（全セル） | 0.005 |

絵文字 vs ランダム方向の fingerprint **分離**（高いほど分離良）：

| 層 | emoji（中央値） | random 対照（中央値） | advantage |
|---|---|---|---|
| **11** | 0.929 | 0.619 | **+0.32** |
| 5 | 0.654 | 0.790 | **−0.17** |

*advantage は各セルの `emoji − random` の中央値であり、2つの中央値列の差ではない。
random 対照は seed で大きくばらつくため両者は一致しない（例：層5 は中央値
advantage −0.17 だが 0.654 − 0.790 = −0.14）。*

つまり、絵文字条件付き方向は**層11 では**一致 RMS のランダム方向より分離が良いが、
**層5 では**そうでなく、（seed でばらつく）ランダム対照がしばしば勝つ。
`fingerprint_reproducibility` gate は全セル中央値の advantage +0.0075 で**かろうじて**
PASS し、その寄与はほぼ完全に層11 由来。

## チャート

`chart/fp_chart.html` は 18 セル（層 × 強度 × seed）を並べた自己完結（CSP 安全）の
ダンベル図。emoji ● vs random 対照 ○ を層でグループ化し、95% split-half CI・hover
ツールチップ・データテーブル・light/dark テーマ付き。ページは 18 セルのデータを
**インライン埋め込み**（CSP 安全・fetch なし）。`chart/fp_chart_data.json` は同じ
データの独立コピー（両方を一緒に編集すること）。いずれも
`results/fingerprint_summary.jsonl` 由来。

## 環境と provenance

- **重みは封印済み v2 アーティファクトと同一。** `scripts/verify_bf16.py` が
  プロジェクト自身の `model_artifact_receipt` を再計算し、
  `mlx-community/Llama-3.2-3B-bf16` @ `60a99aaf…` = 9ファイル・6,434,705,789 バイト・
  `manifest_sha256 dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`
  を確認済み＝凍結 v2 モデルとバイト単位で一致。全 254 パラメータテンソルが `float32`。
- **ライブラリは凍結と異なる**（＝v2 再現ではない）：本実行は
  Python 3.12.6 / torch 2.12.1 / transformers 5.13.0 / numpy 2.2.3。v2 は
  3.13.13 / 2.11.0 / 4.57.6 / 2.4.4 で凍結。
- **Shim**（`scripts/shim/`、`PYTHONPATH` 経由のみ、ディスク上は何も改変しない）：
  - `orjson.py` — クリーン環境に `orjson` が無いための stdlib-`json` 代替。ASCII
    マニフェストではバイト等価（verify ハッシュが一致）だが、その他の出力ハッシュは
    非正規として扱うこと。
  - `sitecustomize.py` — transformers ≥5.13 が mlx-lm の文字列キー tokenizer 登録を
    許容するようにする（MLX 経路のみ関係）。
- 実行は `PYTHONNOUSERSITE=1` でマシンのユーザーサイト「Spiralton」numpy/torch
  monkey-patch 層を無効化し、numerics を素のまま使用。

## 再現手順

このディレクトリ（`sandbox/llama32_3b_bf16_ooc_screen_v1/`）から実行。bf16 モデルが
HF キャッシュにあり、`glyphprobe[torch]` 依存が import 可能なことが前提。

```sh
export HF_HOME=~/.hf_home           # モデルの（キャッシュ）場所
SNAP=$HF_HOME/hub/models--mlx-community--Llama-3.2-3B-bf16/snapshots/60a99aaf43164077157d64bf909b7b61143c6a6d

# 0) 初回ダウンロード（取得時のみオフライン解除）
PYTHONNOUSERSITE=1 PSYCHOID_NET_GUARD=0 HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0 \
  python3 -c "from huggingface_hub import snapshot_download as s; print(s('mlx-community/Llama-3.2-3B-bf16', revision='60a99aaf43164077157d64bf909b7b61143c6a6d'))"

# 1) 重みが凍結 v2 アーティファクトと同一か検証
PYTHONNOUSERSITE=1 PYTHONPATH=scripts/shim:../../src SNAP=$SNAP \
  python3 scripts/verify_bf16.py

# 2) resid_post キャプチャ実演（絵文字 vs neutral）
PYTHONNOUSERSITE=1 PYTHONPATH=scripts/shim:../../src SNAP=$SNAP \
  python3 scripts/capture_llama3b_bf16_transformers.py

# 3) フルのスケール内部スクリーン（../../../runs に出力、gitignore 対象）
PYTHONNOUSERSITE=1 PYTHONPATH=scripts/shim:../../src \
  python3 -m glyphprobe run -c configs/scaled_llama_bf16_transformers.yaml
```

`configs/smoke_llama_bf16_transformers.yaml` は高速（1-seed・1-strength）の sanity 版。

## 構成

```
chart/     fp_chart.html, fp_chart_data.json      — 可視化とそのデータ
scripts/   verify_bf16.py, capture_llama3b_bf16_transformers.py, shim/
configs/   scaled_…（チャートの出所）, smoke_…（高速 sanity）
results/   report.md, summary.json, fingerprint_summary.jsonl, capture_bf16_summary.json
```

生の run 配列（`*.npz`・`interventions.jsonl`）は意図的に**除外**（大きく、非正規
provenance のため）。手順 3 で再生成できる。
