# 同じ24課題での候補文感度分析

[English](CONTEXTUAL_EMOJI_CANDIDATE_WORDING_V0.md)

制限付き取得は完了した。[結果は別文書](CONTEXTUAL_EMOJI_CANDIDATE_WORDING_V0_RESULTS.ja.md)に記す。
以下の設計は、追加スコア取得前の判断をそのまま残している。

状態：追加候補文のスコア取得前、既存の絵文字・単語対照の結果を見た後に
作成した開発用設計。新しい確認用bankでも、否定表現だけを分離する実験でもない。

## 問いと固定する設計

採点する2つの続き文を変更しても、観測した文脈×手がかりの交互作用は残るか。
既存の平均Hは絵文字1.312269、単語2.250543、著者ラベルとの一致はそれぞれ
54/96、60/96だった。この結果だけでは絵文字特有の文脈解釈は確立しない。
まず候補文への測定感度を確かめる。

開発用24ブロック（6 family×4）、元の2文脈、2つの手がかり、絵文字と単語の
両方を維持する。モデル、BF16演算、eager attention、続き文全体の非正規化
対数確率による採点も維持する。生成・学習・介入は計画しない。

次の3組を個別に報告する。

| 組 | 肯定側の続き文 | 否定側の続き文 |
| --- | --- | --- |
| 元の候補 | 元の課題固有の文 | 元の課題固有の文 |
| 明示的否定による目標との適合 | ` This meets my goal.` | ` This does not meet my goal.` |
| 形容詞による目標との適合 | ` This is suitable for my goal.` | ` This is unsuitable for my goal.` |

先頭の空白も入力の一部。eta=+1では肯定文をA、eta=-1ではBに置き、元の向きを
保つ。追加2組は全課題に共通で、familyや結果に応じて選ばない。元の24組は
変更しない。候補文は著者作成で、人による妥当性検証はない。組の名前は略称で
あり、語彙・トークン長・具体性・形態も同時に変わる。純粋な否定効果を特定する
比較とはせず、意味の等価性も主張しない。

## 分母と取得順

- 両carrierを合わせた交差条件の異なるpromptは192。
- 元の交差条件384スコア（絵文字192、単語192）を再利用する。元の手がかりなし
  96スコアは今回の比較に含めない。
- 追加768スコア＝追加2組×24ブロック×2文脈×2 carrier×2変種×2続き文。
- 統合する交差条件は1,152スコア。開発用ブロックは依然24である。
- 重み配置変更の検証として元の交差条件384セルを別途再実行する。
  これは工学的同等性検証であり、独立した追加観測ではない。
- 新しいmodel forward試行の上限は1,152（同等性384＋追加候補768）。
  読み込みと両段階を合わせた時間上限は900秒で、forward間に確認する。
  実行中のforwardの完了は、この時間を超える場合がある。

元のスコアとの同等性検証をすべて先に行う。追加候補は組、ブロック、文脈、
carrier、変種、候補の順。結果に応じた並べ替え、最良の組だけの採用、暗黙の
再試行・再開はしない。全予定セルを完了・失敗・事前検査失敗・未実行として残す。
境界や予算に問題があれば、欠測を補完せず全体集計を未確定にする。
追加の手がかりなし条件はない。候補文が違うため、元の手がかりなしスコアを
追加候補に流用することはできない。

## 炉での制限付き共存

ユーザーはAetherとの空きVRAM共存の検討を明示的に承認した。
2026-10-07の読み取り専用観測では、Aether PID 485817が23,540 MiBを占有し、
空きは8,540 MiBだった。12回の観測でGPU使用率は24〜100%。空きVRAMが
空き演算能力を意味するわけではなく、この観測は資源の予約でもない。

BF16パラメータ全体は約6,128 MiB。decoderの重みをCPUに保持し、decoder blockを
1つずつCUDAへ転送する。埋め込み、共有出力重み、最終正規化、rotary bufferは
CUDAに置く。層hookは各blockの後、エラー時も元のCPU storageへ復帰させる。
変わるのは配置と転送負荷であり、量子化や意図する演算デバイスは変えない。
CUDA上の数値同等性は実測で確認しなければならない。

ソースに結び付けた計算条件は以下のとおり。

- PyTorch割り当て上限2,560 MiB、driver分の許容量512 MiB。
- 割り当て前の空き7,168 MiB以上、採点中は4,096 MiB以上。
- 共存相手は観測済みのPID 485817のみ。新しいpeer PID、状態の読み取り不能、
  空き不足、自プロセス3,072 MiB超過で取得を停止する。peerの正常終了は許容する。
- 各forwardの前後に検査し、開始間隔は最低0.1秒。入力上限96トークン、候補上限
  64トークン、batch sizeは1。
- 元の交差条件384セルすべてで、各トークン対数確率と合計が完全一致した場合だけ
  新候補へ進む。最初の不一致で停止し、許容差拡大や別配置への自動切替はしない。
- 失敗時・完了時は自分の重みを解放する。peerの設定変更、停止、優先度変更、
  研究出力の閲覧、killは行わない。

これらはメモリを予約せず、Aetherの速度への影響がゼロとも保証しない。同時に
発生する割り当て競合や実行中kernelを先取りして防ぐものではない。試行の失敗も
有効な結末とする。基本runtimeの同一性、配置変更、数値の実測同等性は別々に記録する。

## 解析と主張の上限

組ごとにs(c,v)=log P(A|c,v)−log P(B|c,v)、delta_c=s(c,b)−s(c,a)、
H=eta(delta_q−delta_p)とする。H、2つのdelta、向きの交差、絶対的な著者ラベル
一致、同点、4条件すべての一致を報告する。Hが正、効果の交差、絶対的な一致は
異なる結果である。全family平均、負の結果、トークン配置を残す。
配置による除外や、トークン化が一致したという主張はしない。

各ブロック・carrierについて3つのH、平均・範囲・符号の安定性、全組での交差、
ラベル選好の安定性を報告する。各組のHの単語−絵文字差と等重み平均も報告する。
完全な組だけを組・familyの等重みで集計する。p値、bootstrap区間、Hの比、
母集団への一般化は行わない。反復測定で独立した課題数が3倍になることはない。

一貫性があれば、このパネルでの条件付き確率測定の頑健性を補強する。
感度があれば解釈を狭める。いずれも、それだけで絵文字の意味曖昧性解消、
因果経路、自由生成時の挙動、単語に対する優位を確立するものではない。

## 再現用の入口

設定は`configs/contextual_emoji_candidate_wording_v0.json`、候補文は
`data/contextual_emoji_candidate_wording_v0.json`。元の入力、仕様、raw score、
helperはSHA-256で固定する。保護対象の過去2つのtarget bankは開かず、使用しない。

```sh
python scripts/contextual_emoji_candidate_wording_v0.py plan \
  --config configs/contextual_emoji_candidate_wording_v0.json --output /NEW/design.json
python scripts/contextual_emoji_candidate_wording_v0.py prepare \
  --config configs/contextual_emoji_candidate_wording_v0.json \
  --model-path /EXISTING/MODEL --output /NEW/specification.json
python scripts/contextual_emoji_candidate_wording_v0.py audit --specification /NEW/specification.json
python scripts/contextual_emoji_candidate_wording_v0.py run \
  --specification /NEW/specification.json --output /NEW/run --acknowledge-development-only
python scripts/summarize_contextual_emoji_candidate_wording_v0.py \
  --run-dir /NEW/run --specification /NEW/specification.json --output /NEW/analysis.json
```

planはテキストだけを扱う。prepareは既存の固定remote runtimeとlocal tokenizerを
使い、forwardやdownloadは行わない。run直前には再び資源を確認する。
CPUの合成テストで確かめるのは算術と停止・記録処理。実際のGPUメモリ使用量と
同等性は、実CUDA試行だけが検証できる。

## forward開始前の実装修正

ソース`b9e7ad2`での初回試行は基本runtime照合で停止した。同等性検証も追加候補も
forwardは0。384＋768セルすべてを未実行として
`validation/contextual_emoji_candidate_wording_v0/shared_trial/`に保存した。
Pythonの生の辞書と読込済みJSONをそのまま比較していたが、Transformersの
`id2label`の整数キーは保存時に文字列へ変わる。修正版は全フィールド・値を保持し、
JSON表現同士で比較する。全トップレベル項目とネストしたラベル値の改変を拒否する
テストを追加した。これは明示的に別記録とする準備処理の修正で、刺激・採点・
メモリ上限・数値許容差・forward予算は変えない。次の制限付き試行には新しい
ソースに結び付けた仕様と出力ディレクトリを使う。
