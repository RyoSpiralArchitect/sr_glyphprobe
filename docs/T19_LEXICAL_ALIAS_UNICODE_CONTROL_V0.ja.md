# T19 語彙エイリアス × Unicode 記号対照

状態: **実行凍結候補。T19 の model forward も介入もまだ 0 回**。

English companion: [T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.md](T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.md)

## 研究の問い

T18 では、リポジトリ上で未使用だった複合 emoji をそのまま入力すると、
コードポイント表記よりも英語の正式短名を近くに取り出せることが、凍結済みの
後半層で確認された。T19 では、その対応が正式名だけに限られるのかを問う。

> 1 コードポイントの emoji は、正式短名と語彙的に重ならない CLDR
> キーワードも、`U+...` というコードポイント表記より近くに取り出せるか。
> また、同じ傾向は emoji ではない Unicode 記号にどこまで現れるか。

観察実験が登録済みのモデル横断ゲートを通った場合に限り、T19-C へ進む。
そこでは別の source bank から rank 8 の部分空間を学び、さらに未使用の
evaluation bank で `attn_out` と `mlp_out` の因果的寄与を調べる。

対象は、Unicode スカラーを文字列として受け取った言語モデルの内部表現である。
描画された字形の知覚や、人間と同じ意味理解を検証する実験ではない。

## 代替ラベルの定義

`canonical_label` は CLDR 48.2 英語版の `tts` をそのまま使う。
`alias_label` は同じ項目の `default` キーワードから一つを固定する。
両者を小文字化し、ASCII の `[a-z0-9]+` だけを語として抽出したとき、
二つの語集合はともに空でなく、互いに重ならなければならない。選ばれた
エイリアスは、三つの bank 全体で重複しない。

たとえば `birthday cake → dessert`、`video game → controller` のような
対応が入る。いずれも出典を追跡できる CLDR キーワードだが、人手で言い換えの
自然さ、同義性、粒度を評価したものではない。そのため主張では
「人手評価済み paraphrase」ではなく「CLDR キーワードエイリアス」と呼ぶ。

## forward 前に固定した三つの bank

| Bank | 項目数 | 役割 | 凍結時の T19-L forward |
|---|---:|---|---:|
| 観察用 emoji | 55 | 登録済み primary | 0 |
| 観察用非 emoji 記号 | 55 | 対照・secondary | 0 |
| 因果 source emoji | 128 | ゲート通過後に部分空間を学ぶ | 0 |
| 因果 evaluation emoji | 192 | 未使用の介入評価 | 0 |

三つの bank を合わせた 430 項目は、コードポイントもエイリアスもすべて異なる。
凍結後の入れ替え、除外、補充は認めない。

emoji は、Emoji 13.1 以前に導入された fully-qualified の 1 コードポイント
項目に限る。これらの表面形は過去の実験に現れている可能性がある。T19 で
事前固定されているのは、問い、エイリアス割当、endpoint、bank 分割であり、
emoji 表面形そのものの完全な未使用性ではない。

一方、非 emoji 記号にはリポジトリ内の表面形未使用条件を課した。次の条件を
すべて満たすものだけを採用する。

- Unicode スカラー一つである。
- Unicode 一般カテゴリが `S` で始まる。
- Unicode Emoji 17 の `Emoji` property が false である。
- CLDR 英語 annotation と、語彙的に重ならないエイリアスがある。
- commit `31b3bcc5f2a635306ebebeb8b66546135b8ca8b0` の Git blob のうち、
  NUL を含まず厳密に UTF-8 として読める全ファイルに、そのスカラーが一度も
  出現しない。

これはリポジトリを境界とした表面形の未使用性であり、pretraining data に
含まれていないという意味ではない。

## T19-L 観察実験

各項目を四つの文字列表現にする。

1. Unicode をそのまま置いた `glyph`
2. CLDR の正式な `canonical_label`
3. 固定済みの CLDR `alias_label`
4. 大文字の `codepoint_literal`

T10/T18 と同じ九つの model/tokenizer cell、二つの suffix carrier
（`" a"` と `" |"`）、距離 `1, 2, 4, 8`、九つの正規化深度を使う。
batch size は 1。special token と chat template は加えず、指定した suffix
token の hidden state を読む。primary window は T18 から事前に固定した
`.75, .875, 1.0` で、1 項目につき 24 context になる。

各 view を項目方向に別々に中心化し、各行を L2 正規化する。モデルごとの統計量は、
24 context にわたる次の平均である。

```text
top1(glyph → alias) − top1(glyph → codepoint literal)
```

登録済み primary に入るのは観察用 emoji 55 項目だけである。非 emoji 記号、
正式名との比較、emoji と記号の差、全深度曲線、その他の幾何指標は登録済みの
secondary とする。対照側の都合のよい結果で primary を救済することはできない。

## Tokenization-matched intersection

各モデルは二つの component を両方通らなければならない。

- **unrestricted:** 観察用 emoji 55 項目をすべて使う。
- **matched:** glyph、正式名、エイリアス、コードポイント表記の四つの token 数が
  完全に一致する stratum のうち、2 項目以上あるものだけを使う。

unrestricted では glyph kind 内、matched では token 数が完全一致する
stratum 内でエイリアス対応を並べ替える。コードポイントと正式名の対応は固定する。
各 component で 19,999 回の randomization を行い、モデルの p 値には二つの
うち大きい方を使う。さらに、観測差が両方とも `0.02` 以上であることを求める。

トークナイザだけを使った事前監査では、どのモデルでも matched 対象が全体で
63 項目以上、emoji 31 項目以上、記号 32 項目以上残った。九つのトークナイザは
すべて、凍結済み T10 入力列を完全一致で再現した。ただし揃えているのは token
数であり、token identity や tokenizer の設計そのものではない。

## モデル横断判定と因果ゲート

唯一のモデル横断 primary は、T10 から固定している四つの core cell、
Llama 3.2 3B base、Qwen 2.5 7B base、OLMo 2 1B base、Gemma 2 2B IT を使う。
四つのうち少なくとも三つが、モデル IUT と二つの実用下限を同時に通るかを判定する。
Bonferroni partial conjunction の p 値は、core cell の三番目に小さい IUT p 値を
2 倍し、1 を上限とする。

この統計条件と実用条件の積集合が通らない限り、T19-C は開かない。他の五モデルや
secondary endpoint による救済は認めない。

## T19-C 条件付き因果実験

因果設計そのものは T19-L の acquisition 前に固定する。ただし、T19-L が通過し、
admission manifest を commit・push するまでは、source bank と evaluation bank の
forward を一度も実行しない。

- **モデル:** 凍結済み Llama 3.2 3B base の一 cell のみ。T19 の結果ではなく、
  事前に分かっていた hook 互換性と資源条件から選んだ。
- **Source bank:** emoji 128 項目。pipe carrier、距離 1 の glyph と alias を使う。
- **部分空間:** 各 component/depth で、中心化・行正規化した glyph–alias
  cross-covariance の左特異方向から rank 8 を学ぶ。
- **ランダム対照:** source span 内から決定論的に作り、学習部分空間と直交する
  rank 8 のランダム部分空間。
- **Primary site:** block 24 の `attn_out` と `mlp_out`。
- **Secondary site:** block 21 と 27 の両 component。
- **Evaluation bank:** 観察にも source 学習にも使わない emoji 192 項目。

必要性介入では、glyph の component 出力から学習部分空間の座標を除く。
十分性介入では、同じ項目の glyph と codepoint の差を学習部分空間へ射影し、
codepoint の component 出力へ加える。ランダム部分空間で同型の操作を行い、
対照効果とする。zero hook と「除去してから元に戻す」条件は、凍結した数値許容差内で
baseline の最終 hidden state を再現しなければならない。

endpoint は、最終 hidden state における項目単位の alias-minus-codepoint top-1
retrieval である。各 site について、次の二 component の intersection-union test を行う。

```text
必要性: random-subspace の結果 − learned-removal の結果
十分性: learned-patch の結果 − random-subspace の結果
```

二つの調整済み効果と、item bootstrap による二つの 95% 下限がすべて `0.02` を
上回ることを求める。片側 sign-flip test は二つとも通過し、さらに二つの primary
site 間で Holm 補正を通らなければならない。engineering control も必須である。
失敗した場合はそのまま残し、モデル、rank、深度、carrier、subset、endpoint を
差し替えない。

## 想定する落とし所

- **T19-L 陽性、T19-C 陽性:** atomic emoji とより広い CLDR 語彙近傍との対応、
  および凍結済み後半 component/subspace cell の因果的寄与を、限定された範囲で支持。
- **T19-L 陽性、T19-C 陰性:** 語彙対応は再現したが、提案した低 rank の後半
  component 機構は支持されない。
- **unrestricted 陽性、matched 陰性:** tokenization で説明できる余地が残るため、
  因果ゲートは閉じる。
- **emoji と記号がともに陽性:** emoji 固有の意味ではなく、より広い Unicode
  lexicalization の可能性を secondary evidence として報告する。
- **emoji 陽性、記号は弱い:** 登録済み secondary 比較と不確実性に限定して、
  emoji–symbol の違いを報告する。
- **T19-L 陰性:** 正式名から語彙的に離れた CLDR keyword へ一般化しなかったという、
  範囲を限定した負の結果として atlas 全体を残す。

## 実行ゲート

1. 出典に固定した selection と、互いに交わらない三つの bank を監査する。
2. 観察・因果の zero-forward design receipt を作る。
3. 観察用九モデルと因果用一モデルの tokenizer preflight を行う。
4. config、selection、script、test、英日 protocol、receipt、T10/T18 binding を凍結する。
5. 凍結 commit を `origin/main` へ push する。
6. model compute の直前に furnace の空きを再確認する。
7. 九つの T19-L cell を取得・封印し、登録済みゲートを解析する。
8. ゲートが開いた場合に限り、因果 admission manifest を commit・push する。
9. source bank から部分空間を固定し、その後で未使用 evaluation bank に介入する。

raw activation は furnace の scratch にだけ置く。Git に入れるのは、compact summary、
analysis、hash、英日レポートだけである。

## コマンド

```bash
python scripts/t19_lexical_alias_unicode_control_v0.py audit-selection
python scripts/t19_lexical_alias_unicode_control_v0.py audit-freeze --require-pushed
python scripts/t19_lexical_alias_unicode_control_v0.py run-role \
  --role MODEL_ROLE --model-path MODEL_SNAPSHOT --output-root RUN_ROOT
python scripts/t19_lexical_alias_unicode_control_v0.py summarize-role \
  --role MODEL_ROLE --output-root RUN_ROOT --summary-root SUMMARY_ROOT
python scripts/t19_lexical_alias_unicode_control_v0.py analyze-summaries \
  --summary-root SUMMARY_ROOT --output ANALYSIS_ROOT

# 条件付き。push 済みの go manifest がある場合だけ実行する。
python scripts/t19_lexical_alias_component_causal_v0.py run-source \
  --model-path LLAMA_SNAPSHOT --output-root SOURCE_ROOT
python scripts/t19_lexical_alias_component_causal_v0.py run-evaluation \
  --model-path LLAMA_SNAPSHOT --source-root SOURCE_ROOT --output-root EVAL_ROOT
python scripts/t19_lexical_alias_component_causal_v0.py analyze \
  --source-root SOURCE_ROOT --evaluation-root EVAL_ROOT --output CAUSAL_ANALYSIS_ROOT
```

文章と差がある場合は、YAML contract、JSON manifest、実行可能な audit を正とする。
