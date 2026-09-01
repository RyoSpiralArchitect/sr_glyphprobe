# T20-C: 最適化部分空間による因果語彙テスト (v0)

[English](T20_LEXICAL_ALIAS_OPTIMIZED_SUBSPACE_CAUSAL_V0.md) | [T19プロトコル](T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.ja.md)

プロトコル: `glyphprobe-t20-lexical-alias-optimized-subspace-causal-v0`
設定: [`configs/t20_lexical_alias_optimized_subspace_causal_v0.yaml`](../configs/t20_lexical_alias_optimized_subspace_causal_v0.yaml)
実行系: [`scripts/t20_lexical_alias_optimized_subspace_causal_v0.py`](../scripts/t20_lexical_alias_optimized_subspace_causal_v0.py)
独立検証: [`scripts/validate_t20_lexical_alias_optimized_subspace_causal_v0_result.py`](../scripts/validate_t20_lexical_alias_optimized_subspace_causal_v0_result.py)

## 問い

登録済み T19-C は、低ベースライン・単一文脈・positive control なしのエンドポイントの下で、
固定 rank-8 遅層コンポーネント説をひとつ棄却した。T20-C はその否定が残した先鋭化された問いを立てる:
**同じ凍結ソースバンクから交換介入最適化で学習できる rank-8 部分空間のうち、
保留評価集合の glyph→alias 検索に対して必要かつ十分なものは遅層サイトに存在するか。
そしてそのテストはそもそも勝ち得たのか（全表現交換の天井で較正して測る）。**

## T19-C からの差分は正確に5点

1. **最適化構成。** 検定対象の部分空間は、凍結済み 128 項目ソースバンク上の勾配交換学習
   （自項目 alias への InfoNCE ＋ necessity ヒンジ）で学習する。96/32 の固定分割、3シード、
   シード選択規則は事前固定。T19 の閉形式 cross-covariance 規則と span 内ランダム統制を
   同一サイトで比較対象として併走させる。
2. **残差ストリームサイト。** ブロック 21/24/27 の `resid_out` を6つのコンポーネントサイトに追加。
   主要サイトは `resid_out@21` と `resid_out@24`（Holm は2つ）。ブロック27残差は読み出しに隣接し
   十分性がほぼ自明になり得るため副次。
3. **成分ゲート判定。** necessity / sufficiency は alias 検索成分のみで判定（ランダム基底で調整）し、
   codepoint 自己検索ガード（学習パッチ下で ≥ 0.90）を課す。表現破壊が十分性として通ることを防ぐ。
   T19 の複合エンドポイントは連続性のため併記。
4. **新鮮・拡大・多文脈評価。** T19/T20 のフォワード履歴ゼロの新鮮なアトミック絵文字 384 個を、
   4文脈（pipe/article キャリア × 距離 1, 4）で読む。各文脈は 384-way 検索。項目値は文脈平均。
   登録フロアは 0.02 のまま。
5. **天井 = positive control。** 全サイトに全表現交換条件（glyph→codepoint / codepoint→glyph）。
   登録解釈規則: 十分性天井が 0.06 未満のまま落ちた主要サイトは
   「このエンドポイントでは較正不能」と記録し、低ランク説の反証とは扱わない。
   天井の値が否定判定を肯定に覆すことはない。

## アイテムバンク

- ソース/学習: 凍結済み T19 `causal_source_items`（128個）をそのまま使用。
- 評価: ハッシュ固定の Unicode 17.0 / CLDR 48.2 ソースから凍結済み T19 ビルダーを再実行し、
  凍結 T19 選定マニフェストと SHA-256 が**バイト一致**することを確認した上で、
  未使用残余（579個）から凍結 round-robin サンプラで 384 個を抽出。
- 非絵文字シンボルのプールは T19 で枯渇（55/55 使用済み）のため T20 に腕はない。

## ゲート系列

1. `build-selection` — T19 再現のバイト一致監査、新鮮バンク抽出、フォワード0。
2. `audit-design` / `tokenizer-preflight` — 構造・トークナイザ受領書、フォワード0。
3. `build-freeze` — 設定・選定・コード・テスト・文書・両受領書の SHA-256 マニフェスト。
   コミットして push、`audit-freeze --require-pushed` 必須。
4. `admit-go` — 検証済み T19-C 解析、T19 freeze/go 連鎖、T20 freeze、ゼロカウンタを要求。
   実行系は自身の SHA-256 を記録し、以後変更されると実行を拒否する。
5. `run-training` — ソース捕捉（384 フォワード）＋交換学習。ソースバンクのフォワードのみ。
6. `run-evaluation` — 評価フォワード 32,256、介入行 124,416、台帳付き封印。
7. `analyze` → `validate-analysis` → 独立バリデータ。

## 判定

主要サイトごとに: 調整済み necessity / sufficiency の平均 ≥ 0.02 かつブートストラップ下側95% > 0.02、
片側符号反転 p 値（主要2サイトに Holm）、自己検索ガード ≥ 0.90、
zero-hook / remove-restore の厳密工学チェック。
評決は `positive` / `negative_with_informative_ceiling` / `uncalibratable_at_endpoint`。

## 主張境界

設定ファイルの `claim_boundary` を参照。特に、行動エンドポイントは意図的に対象外
（forced-choice 挙動は T16-OSC の記録が担う）。いかなる結果も、視覚知覚・人間的意味・
回路の一意性/完全性・スケール則・モデル母集団一般化を認可しない。
