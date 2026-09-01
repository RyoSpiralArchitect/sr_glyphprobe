# T16-UTF-X1 系列長・配列variant stress test

[English](T16_UTF_SCALE_VARIANTS_V1.md) · [親実験 T16-UTF](T16_UTF_IDENTITY_MIXING_V0.ja.md)

T16-UTF-X1は、T16-UTFから派生した大規模な探索実験である。先の実験で見えた、
完全同一文字列の反復、同じ構成family内の混合、異なる構成familyをまたぐ混合の差が、
系列を大きく伸ばし、model/tokenizer cellを増やしても残るかを調べる。親実験では
切り分けられなかった、itemの順序、区切り文字、完全同一UTF anchorの位置も、
それぞれ独立したlaneとして測る。

設計全体、9 roleすべてのtokenizer receipt、最終実行manifestをcommitしてpushするまで、
T16-UTF-X1のactivation outcomeは開かない。

## 固定したgrid

元のpanelは変えない。Unicode構成family 6種から各4 item、合計24個の完全同一文字列を
使う。すべてのcellで、4つの固定wrapperと4つのrotationを組み合わせる。

Stress testは、互いに重ならない3つのlaneに分けた。

- **Scale:** `n = 1, 2, 3, 4, 5, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192,
  256, 384, 512`。完全clone、同じfamily内のcycle、familyをまたぐcycleを比較する。
- **Order:** `n = 8, 16, 32, 64, 128, 256`。Family内・family横断の各multisetを、
  forward、tail反転、同一itemごとのblock化、tail両端の交互配置、固定seed 2種のshuffleで
  並べる。対になった比較では、先頭itemと完全一致するitem multisetを保つ。
- **Position:** 同じ6つの系列長を使い、family内またはfamily横断の背景にanchorを一つだけ
  入れる。位置は先頭・中央・末尾の3通りで、item multisetは完全に一致させる。

Orderとpositionには、区切りなし、ASCII space、comma-space、改行、ASCII pipeの5条件を
置く。1 modelあたり57,312 record、9つのmodel/tokenizer cellを合わせて515,808 record。
各modelのrunは11個のatomic chunkに分け、競合でyieldしても完了済みchunkを失わない。

## Model cellとendpoint

対象は、T10/T13ですでに固定しruntime preflightを通した9 roleである。Qwen2.5の4 size、
Llama 3.2 3B、OLMo 2 1B、SmolLM2 1.7B、Gemma 2 2B IT、Mistral 7B Instruct v0.3を使う。
訓練data、tokenizerの系譜、model familyを共有しているため、独立した再現ではなく、
固定済みcellの範囲に限った結果として扱う。

正規化深度0.25、0.50、0.75、1.0で、共通wrapperの最終tokenにおけるdecoder blockの
raw outputを取得する。生成も介入も行わない。

## Tokenizationとpaired control

最終freezeの前に、固定snapshotから全promptをlocal tokenizeする。Receiptには、完全な
token ID列、token数、prompt全体のtoken multiset hash、model artifactの同一性、roleごとの
最大context長を結びつける。8,192 tokenを超えるpromptが一つでもあればfail closedとする。

完全一致するitem multisetはUnicode文字列に対するcontrolであって、tokenizer controlではない。
そこで、順序と位置の各paired contrastについて、token数の完全一致率に加え、より強い
「prompt全体のtoken multiset」完全一致率も報告する。

## 記述endpoint

- Scale: `n=1`からのclone growth、同じ`n`のcloneから測るfamily内変位とfamily横断変位、
  およびcross-minus-within。
- Order: family、`n`、separator、wrapper、anchor、item multisetを固定し、forward-tailからの
  cosine変位を測る。
- Position: 背景、`n`、separator、wrapper、item multisetを固定し、anchor-firstからの変位を
  測る。
- Separator: item順序とその他の因子を固定し、区切りなしからの変位を測る。

主要な記述単位はsystem × rotation × wrapperで、model-depth cellごとに96単位ある。
95% equal-tailed区間は、systemで層別した10,000回のbootstrapで求める。`n`別中央値も
すべて報告するが、outcomeを見た後に二値gateを作ることはしない。

## 主張の境界

T16-UTF-X1が記述できるのは、この固定gridを条件としたhidden-state geometryと、patternの
安定性までである。Tokenizer非依存のUnicode合成、emojiの意味理解、因果回路、
instruction tuningの効果、scaling law、独立したmodel再現、architectureまたはmodel母集団への
一般化は主張しない。

保護対象のP2/C1 target bankは開かず、tokenize、sample、利用のいずれも行わない。

## 実行surface

```bash
python scripts/t16_utf_scale_variants_v1.py audit-design
python scripts/t16_utf_scale_variants_v1.py preflight-role \
  --role qwen25_0p5b_base_bf16 \
  --output validation/t16_utf_scale_variants_v1/tokenizers/qwen25_0p5b_base_bf16.json
python scripts/t16_utf_scale_variants_v1.py aggregate-preflight \
  --directory validation/t16_utf_scale_variants_v1/tokenizers \
  --output validation/t16_utf_scale_variants_v1/tokenizer_preflight.json
python scripts/t16_utf_scale_variants_v1.py freeze
python scripts/t16_utf_scale_variants_v1.py audit-freeze --require-pushed
```

CUDA取得は`run-role`で実行する。外部GPU processを検知したらexit code 75でyieldし、完了済みの
chunk境界からのみ再開する。Raw hidden arrayは炉に残し、Gitへ収録するのはcompact receiptと
解析結果だけとする。
