# T22 CPU語彙比較：露出済み8項目の記述結果

[English](T22_CPU_LEXICAL_RESULTS_V0.md) | [凍結した仕様](T22_CPU_LEXICAL_CANARY_V0.ja.md) | [第2論文の考察](PAPER2_DISCUSSION_NOTES_V0.ja.md)

2026年10月20日06:41（日本時間）に完了。事前に選んだ露出済み8項目、両carrier、
両固定donor、4操作すべてを保持した。仮説検定・効能screen・母集団の信頼区間・
確認実験の判定は行わない記述的な測定である。384項目探索は未実施で、
この8項目の効果の符号で採否判断や再調整をしない。

## 主な観測

今回の条件付けた計算では、Vのみの置換でも語彙readoutが変化した。
位置調整済みmargin decrementの平均はVが+0.001805、Kが+0.000437、KVが+0.000899。
KVはKとVの和にはならず、`Delta_KV - Delta_K - Delta_V` の平均は **−0.001343**。
この8項目の平均から、大きなpanel全体でVが優位だとか、下流routingと独立してVが意味を運ぶとは結論しない。

各指標は、先に同一batch slotのneutral参照を引く。Deltaはsuffixの効果−glyphの効果を、
各target内で2 carrier・2 donorについて平均したもの。
marginのDeltaが正なら、同数のsuffix置換よりglyph置換の方が、正解語と最強競合語の差を大きく下げたことを示す。
Galleryは正解aliasと固定128 source aliasであり、語彙全体や生成の指標ではない。

| 操作 | 位置調整済みmargin低下の平均 | 項目間の標本SD | 項目の範囲 | glyphの絶対margin低下 |
|---|---:|---:|---:|---:|
| Reference | 0 | 0 | 0〜0 | 0 |
| K | +0.000437 | 0.001765 | −0.002796〜+0.002813 | +0.000193 |
| V | +0.001805 | 0.003647 | −0.003502〜+0.009042 | +0.002353 |
| KV | +0.000899 | 0.004175 | −0.007956〜+0.005689 | +0.001340 |

3操作とも正の項目が6、負の項目が2だった。非加法性の比較値は標本SDが0.001894、
範囲が−0.003930〜+0.001195。条件の反復で標本を8 targetより増やさず、
統計的な勝者となる操作は宣言しない。

| 固定canary index | K Delta | V Delta | KV Delta | KV − K − V |
|---|---:|---:|---:|---:|
| 0 | +0.002813 | +0.001745 | +0.000627 | −0.003930 |
| 1 | +0.001724 | +0.000970 | +0.003889 | +0.001195 |
| 2 | +0.001692 | +0.002849 | +0.002592 | −0.001948 |
| 3 | +0.000255 | +0.009042 | +0.005689 | −0.003608 |
| 4 | −0.002796 | −0.003502 | −0.007956 | −0.001658 |
| 5 | +0.000268 | +0.002683 | +0.002625 | −0.000327 |
| 6 | −0.001101 | −0.001351 | −0.001487 | +0.000966 |
| 7 | +0.000642 | +0.002004 | +0.001211 | −0.001436 |

## 正解語・競合・rank・attention

marginの分解は記録したfloat64精度で厳密に一致した。
以下は位置調整済みの成分であり、未調整の正解語cosine変化ではない。

| 操作 | 正解cosineのDelta | 最強競合cosineのDelta | 差：marginのDelta |
|---|---:|---:|---:|
| K | −0.009472 | −0.009909 | +0.000437 |
| V | +0.001094 | −0.000711 | +0.001805 |
| KV | −0.008112 | −0.009010 | +0.000899 |

Vの平均調整marginには正解語・競合語の両成分が寄与した。
K/KVでは成分の方向が異なり、marginだけでは変化を説明し尽くせない。
最強の競合語は行によって変わり得る。そのidentityと全129 score、
対応donorとのmargin、正解rankも保存した。

位置調整済みtop-1 decrementはK/KVが−0.0625、Vがゼロ。
glyphの絶対top-1 decrementも同じ平均だった。ゼロでないtop-1比較値はindex 4の
項目内−0.5だけから生じ、他の7項目はゼロだった。
したがって、平均margin decrementが正であることを、対応するtop-1の低下とは報告しない。
固定129語gallery内の記述値であり、性能上の利益や生成の結果とはしない。

Vのみの置換は、同じlayer入力におけるlocal baselineからattention weightを変えなかった
（最大差は厳密にゼロ）。一方で、activeとneutralのattentionはblock 22より後で変わった。
8項目・carrier・donor・2位置群で平均したheadごとのweight L1差は、block 23が0.008635、
block 27が0.028619だった。下流queryの変化に関する留意点が実測にも表れた。
Kを純粋なrouting、Vを純粋な意味とはしない。参照attentionを固定する比較は別の実験となる。

## 取得・検査・証拠

元の介入配列を、新しい介入forwardなしで再利用した。追加取得は単独batchのalias 272 forwardと、
stock glyphの全状態再現16 forward。16個の全stock tensorはすべて完全一致した。
元の9ファイルのmodel manifestを取得前後に検証し、固定BF16 CPU runtimeとNumPy版を
スコア算出前に凍結した。取得時間は最初のmanifest検査後116.76秒で、model loadと
最後のmanifest検査を含み、最初のmanifest検査時間は含まない。
Process peak RSSは6,015,164,416 bytes（5.60 GiB）。

新しい合成テストは **16件成功・skipゼロ**。
RunnerやTorchをimportしない独立コードで、**512行の66,048 cosine**、
全項目の比較値と要約、CSVの整列、attention診断を再計算した。
Cosineの最大誤差は `4.6629367034256575e-15` で、固定した算術許容差 `1e-12` 未満。
Referenceの効果は厳密にゼロで、記録したmargin分解誤差もゼロ。
監査は保存していない今回のstock tensorやモデルファイルの検査を繰り返すものではなく、
それらはソースに結び付けた取得時のassertionとして残る。

- [結果receipt](../validation/t22_cpu_lexical_canary_v0/results/result.json)、
  SHA-256 `87dd3ef5ad61f5c6486d5096219126b8f1775bcc258b20685878ebcad2e2ace2`。
- [独立監査](../validation/t22_cpu_lexical_canary_v0/independent_validation.json)。
- [凍結仕様](../validation/t22_cpu_lexical_canary_v0/acquisition/specification.json)、
  SHA-256 `e6da21348028f8fffe6bda879336beeffcbf515e1862271dada2db6f4bf56067`。
- [取得receipt](../validation/t22_cpu_lexical_canary_v0/acquisition/acquisition_receipt.json)、
  SHA-256 `5bac71106134a2c5f56cbc5c8e371e5e48832e084ca233a2d020ffa7598d10b2`。
- [byte単位で同一なarchiveのmanifest](../validation/t22_cpu_lexical_canary_v0/archive_manifest.json)。

Archiveにはalias・行ごとのreceipt・raw cosine score・参照との差分・CSV・attention診断を保存した。
実装検証の親配列とreceiptもbyte単位で同じまま
`validation/t22_cpu_engineering_v0/canary/` に保存し、
[archive manifest](../validation/t22_cpu_engineering_v0/canary_archive_manifest.json)を添えた。
元の取得結果は `runs/t22_cpu_canary_v0/` に保持している。
過去GPUとの一致、codepoint gallery対照、絵文字特異性、挙動上の利益は未確立。
大規模探索は、このcanary平均によらず凍結した候補と固定galleryを使う。

## 別のcheckoutでの数値再計算

NumPyをインストールし、任意のcheckoutのrootで、未使用の出力先を指定する：

```bash
python3 scripts/validate_t22_cpu_lexical_results_v0.py \
  --acquisition validation/t22_cpu_lexical_canary_v0/acquisition \
  --analysis validation/t22_cpu_lexical_canary_v0/results \
  --parent-run validation/t22_cpu_engineering_v0/canary \
  --validation-receipt validation/t22_cpu_lexical_canary_v0/synthetic_validation.json \
  --expected-specification-sha256 e6da21348028f8fffe6bda879336beeffcbf515e1862271dada2db6f4bf56067 \
  --output /tmp/t22-lexical-audit-NEW.json
```

2つの移設optionはfileの場所だけを変更する。元の仕様・receipt・source・配列の
hash検証はすべて必須のまま。モデル、Torch、元のworkspace path、network接続、
保護対象bankは不要。保存データの数値監査を再計算するもので、モデル状態の再取得ではない。
凍結した取得・scoring runnerは元の絶対pathを保っている。

最初の独立監査は変更せず保存し、そのvalidatorはcommit
`83b1a2220822b11ecbf190016ff480c6bb9de42d` にある。
移設に対応したvalidatorには別の
[再計算receipt](../validation/t22_cpu_lexical_canary_v0/portable_validation.json)を付ける。
どちらのreceiptも、2回目の実験取得を意味しない。
