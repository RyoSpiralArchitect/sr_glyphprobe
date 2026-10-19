# T22-E 提案：経路の主張を広げる前に K と V を分ける

[English](T22_KV_DISSECTION_FIRST_STEP_V0.md) | [T21 結果](T21_GLYPH_CONTEXT_PATH_RESULTS_V0.ja.md) | [最終証拠監査](POST_REVIEW_EVIDENCE_RESULTS_V0.ja.md)

状態：**合成入力による実装検証を実装済みの、2026-10-19 の方針メモ。
凍結済みの確認実験プロトコルではない**。
T22 の実項目を用いるモデル取得実験は未実施。現在の論文、T19/T20/T21 の判定、過去の証拠は変更しない。

## 方針と理由

第一歩は **key-only / value-only 介入の canary 検証**とする。実装検証を通過したら、
評価済み項目で範囲を限定した探索比較を行う。問いは、同じ block 21 の codepoint
読み出しリセット後に、key を直接置換せず絵文字位置の value を変えるだけでも
語彙 margin が動くか、それが key-only・key/value 同時置換とどう異なるか。

T21-C が示したのは条件付きの margin への寄与であり、検索正解率の改善ではない。
位置調整済み decrement/restoration 平均は 0.002326/0.002267、絶対効果の top-1
平均は両方ともゼロ。最終監査では margin を正解キーワードと最大競合の変化へ分解したが、
新しい確認的検定は行っていない。実装では依然として K と V を同時置換しており、
局所的な注意重みの変化、重み付けされるベクトルの変化、その相互作用を切り分けていない。

この問いは T21 の読み出しと文脈を保ち、介入の一要因だけを変えられる。
大きな記号パネル比較や新しい生成課題も次の候補だが、同時置換に残るこの曖昧さは解消しない。

## 最小の具体的な成果物

探索用 adapter を別に実装し、まず合成入力の小型 Llama で検証する。
過去の T21 adapter や receipt は書き換えない。局所介入は次の4条件を持つ。

| 条件 | 選択した過去位置で置換するもの |
| --- | --- |
| 参照 | K・V とも置換しない |
| K | RoPE 適用後の key のみ |
| V | value のみ |
| KV | 両方。T21 と同じ操作 |

同じ target・donor tensor を用い、単一の attention 演算で4条件を検証する。
V-only では入力 query・key・mask・attention weight が不変、K-only では入力 value
が不変であることを要求する。標準経路との一致、同一 batch slot の no-op、
donor 置換後の元値復元、self/future K/V の不変、非読み出し位置の attention 出力の
不変を確認する。GQA の head 処理、RoPE 位置、causal mask を保つ。
診断用の重みには、参照経路の重みを流用せず、介入計算で実際に使用した重みを記録する。

これは **局所的な**不変条件である。複数 block に介入すると、V-only でも読み出し状態の
変化を通じて後段 query と注意重みが変わり得る。経路全体を固定した実験とは呼ばず、
K を純粋な経路、V を純粋な意味内容と同一視しない。参照 attention weight 自体を固定する
実験は、さらに別の条件を課す問いとして後に設計する。

合成検証後は、既に露出済みの T21 canary の8項目をそのまま使う。
checkpoint/revision、BF16 runtime、block 21 reset、blocks 22–27、distance 8 の
2 carrier、事前指定された token 数一致の2 donor、gallery、同一 slot の neutral
reference を保つ。KV の再現確認では過去の batch 配置を維持し、追加条件は別に取得する。
絵文字位置と同数 suffix 位置の両方を検証する。過去の出力との再現照合には元の配列と
互換 runtime が必要で、receipt だけでは配列レベルの照合にならない。
新しい出力は過去のディレクトリ外に版を付けて保存する。

## 実装検証を通過した後の探索測定

評価済み T20 pilot の384項目と、固定の128項目 source donor/gallery を使用する。
新規取得前に正確な specification と runner hash を固定する。
新しい結果に基づく layer・donor・項目選択をしない。anchor 21、distance 8、
両 carrier・両 donor を維持し、target 項目内で平均する。
条件や文脈の反復で標本数を増やさない。再利用から未使用集団への確認的推論は行えない。

K・V・KV の操作 X ごとに、M を元の「正解キーワード cosine − 固定 gallery の最大競合
cosine」とし、各条件の同一 slot neutral reference を差し引く。
探索対象の位置調整済み decrement は次とする。

`Delta_X = 項目平均[M(suffix 置換 X) − M(絵文字位置の置換 X)]`。

K・V・KV を項目単位の不確実性とともに並べ、
`Delta_KV − Delta_K − Delta_V` を非加算性の記述的 contrast として示す。
比率を機構の説明割合とせず、媒介要素の加算性も仮定しない。
絶対 decrement、正解キーワード cosine、最大競合 cosine とその identity、
正解対 donor margin、top-1、layer/head ごとの実際の attention mass も保持する。
これらは donor 方向への変化や競合の変化を診断するが、単独で意味輸送を立証しない。
結果を見た後に副次評価を主評価へ昇格させない。restoration と行動課題は最初の探索比較に含めない。

## 継続・停止と次の判断

- 実装検証の失敗、または KV 再現の不一致：科学的解釈を止め、数値・runtime・adapter の差を調べる。
- 実装検証を通過：最初の8項目の効果の符号によらず、事前指定した探索パネルを完了する。
  canary 8項目を有効性の選抜に使わない。
- V-only に効果：後段の経路変化に関する留保を保ち、独立した value 経路検証を設計する動機とする。
- K-only または非加算性が主：内容経路と解釈する前に注意重みと donor 適合性の対照を優先する。
- 小さい、または不精確な効果：その限界を報告し、都合のよい layer や endpoint に差し替えない。
  この探索メモから確認的判定は出さない。

確認実験の前には、新しい適格集団、開発・評価分割、実質的効果の閾値、標本数、
多重性処理、判定規則を定める。元の954項目 matching に未使用分は残っておらず、
T21 の195項目も露出済み。seed や carrier を変えても項目が未使用になるわけではない。
過去の P2・廃止済み C1 target bank を再度開かず、それらを読む旧 selection/exposure
scanner も実行しない。絵文字特異性には非絵文字の経路対照が、対応する性能改善の主張には
順位または行動の検証が引き続き必要である。

## 今回確認した証拠と実行範囲

CPU 上の T21 compact replay は195項目・bootstrap 20,000反復で成功し、
最大数値誤差は0。5 contrast の margin 分解 replay も成功し、
最大誤差は 4.163336342344337e-17。保存済み scalar 証拠の検査であり、
raw state の取得や科学的な独立追試ではない。

独立した adapter は
[`t22_kv_dissection_v0.py`](../scripts/t22_kv_dissection_v0.py) に実装した。
過去のソースを変えず、T21 の capture/reset hook を再利用する。
テストはランダムな小型 Llama、独立した GQA attention 計算、CPU FP32/BF16 を使用する。
操作の分離、実際に返す重み、全 query の causal mask、非読み出し出力、標準経路との一致、
roundtrip、元の KV batch 配置との一致を検証する。
V-only は局所的な注意重みを保つが、後段 query は変わり得る。
これらの合成結果から、絵文字の語彙効果は測れない。

ソースに結び付けた実装検証 receipt は
[`synthetic_validation.json`](../validation/t22_kv_dissection_v0/synthetic_validation.json)
に生成する。露出済みの8項目は
[`canary_specification.json`](../validation/t22_kv_dissection_v0/canary_specification.json)
で固定するが、これは入力の指定であって取得の許可・実行ではない。
[`runtime_preflight.json`](../validation/t22_kv_dissection_v0/runtime_preflight.json)
に実モデル用の不足要件を記録する。

再現はリポジトリ直下で次を実行する（未使用の出力パスを選ぶ）。

```bash
.venv/bin/python -m pip install --no-cache-dir 'torch==2.13.0+cpu' \
  --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install --no-cache-dir 'transformers==5.15.0'
.venv/bin/python scripts/validate_t22_kv_dissection_v0.py \
  --output /tmp/t22-synthetic-validation.json
.venv/bin/python scripts/t22_kv_dissection_v0.py prepare-canary \
  --output /tmp/t22-canary-specification.json
.venv/bin/python scripts/t22_kv_dissection_v0.py preflight \
  --output /tmp/t22-runtime-preflight.json
```

検証器は skip・不完全な suite・検証中のソース変更を拒否し、継承された pytest の
選択オプションによって部分実行が成功扱いにならないようにする。
receipt/specification は既存ファイルを上書きしない。
preflight は不足要件があるとモデル forward なしで終了コード2を返す。
過去 canary を指定した場合は元の receipt との一致と source/chunk hash 全体の検証を要求する。
有限値の配列や JSON receipt だけではこの条件を満たさない。

現在の環境には Torch 2.13.0+cpu と Transformers 5.15.0 を導入済み。
GPU device はなく、調査した workspace/cache にはローカル Llama checkpoint と
元の canary raw 配列がない。T21 の GPU runtime は RTX 5090 上の
Torch 2.13.0+cu132・Transformers 5.15.0・BF16 だった。
CPU 合成検証は完了したが、過去 checkpoint の再現、実モデルでの8項目 canary 取得、
384項目の探索比較は **未実施**。実モデル用 canary driver も未実装で、
資源が利用できた際には指定済み gate を強制する形で実装する。
この成果物を実験全体の実行完了とは扱わない。
