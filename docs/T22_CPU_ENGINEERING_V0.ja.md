# T22 の CPU 実装検証経路

[English](T22_CPU_ENGINEERING_V0.md) | [最初の K/V 方針](T22_KV_DISSECTION_FIRST_STEP_V0.ja.md)

状態：**CPU で再取得する検証経路。過去の GPU 出力の再現は、別の未解決作業として維持する**。
以前の実行可能性評価を拡張するが、T19/T20/T21 の結果・gate・保存済み receipt は変更しない。
実装の一致は絵文字の語彙効果を示す証拠ではない。

その後の状態：別段階の[8項目の語彙解析](T22_CPU_LEXICAL_RESULTS_V0.ja.md)は完了した。
この文書は実装検証段階とその境界を記録する。
8項目の親配列とreceiptは、別checkoutでの数値監査のため
`validation/t22_cpu_engineering_v0/canary/` にも保存した。

## repo に保存されているもの

T21 pilot の specification は、モデル `mlx-community/Llama-3.2-3B-bf16` の
revision `60a99aaf43164077157d64bf909b7b61143c6a6d` と、全9ファイルのサイズ・
SHA-256 を固定している。合計 6,434,705,789 bytes、manifest SHA-256 は
`dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`。
露出済み canary 項目ごとの token 列と2 donor も保存されている。
保護対象 bank の走査や、新しい項目の選択は不要。

T21 の元 `source_states.npz` と canary の `states.npz` は追跡されていない。
取得 receipt は hash を結び付けるが、hash から配列は復元できない。
他研究の NPZ は repo に存在するので、欠けている T21 の配列と混同しない。

## 現在の接続状況と CPU 資源

ユーザー指定の SSH 接続先は private LAN アドレス。この cloud からホスト鍵の厳密検証と
batch mode を指定して接続すると、認証・ホスト鍵検証より前に **Connection refused**
となった。指定の known-hosts ファイルもここにはない。
標準 SSH include に所有権の問題があったため、接続試験では空の client 設定を用いたが、
明示的な `StrictHostKeyChecking=yes` は維持した。ホスト鍵検証を無効化せず、
システム設定も変更していない。この結果から、ユーザーの LAN 内からの到達性は判断できない。

Hugging Face の HTTPS は当初 proxy CONNECT 403 だったが、ユーザーが環境を
Publish した後、`us.aws.cdn.hf.co` への redirect を含め、固定モデルの取得に成功した。
現在保存されている network policy は unrestricted であり、これはユーザー設定の観測結果で、
downloader による変更ではない。モデル認証の失敗は観測されず、新しい secret も不要だった。

CPU は5 core が見える EPYC 9V74 で AVX512_BF16 を持ち、CPU quota は4 core、
Torch の MKLDNN は有効。メモリ上限は32 GiB。
実 BF16 checkpoint の load は成功した。固定1項目の時間計測は9つの実装検査すべてを通過し、
項目の計算に1,915.38秒（31.92分）、model manifest の検査と load を含む呼び出し全体に
2,008.07秒かかった。Process peak RSS は6,159,065,088 bytes（5.74 GiB）。
過去実装の最初の88行 active forward は271.21秒だった。
その後の8項目取得は7,709.64秒（2時間8分30秒）、peak RSS は
6,195,048,448 bytes（5.77 GiB）で完了し、最初の4〜5時間という見積もりを下回った。
現在の環境での実測であり、将来の実行時間を保証するものではない。
Torch 2.13.0+cpu、Transformers 5.15.0、eager attention を使い、量子化・remote code は使わない。
元の GPU 環境へ CPU Torch をインストールしない。

## 固定 artifact の取得と検証

ネットワーク設定の適用後、`/workspace/sr_glyphprobe` から実行する。

```bash
.venv/bin/python scripts/fetch_t22_pinned_model_v0.py \
  --output /workspace/models/llama32_3b_bf16_t21
```

現在の環境では、このパスに検証済み9ファイルを取得済み。
新規取得には、同じ `--output` を受け付ける
`scripts/fetch_t22_pinned_model_ranges_v0.py` も使える。
最大4本の HTTPS range request を並列実行し、厳密な range response と同じ最終ファイル全体の
hash を要求してから各ファイルを公開する。不完全な response body は回数制限付きで再試行する。
range cache は不変のモデルディレクトリの外に保存する。

downloader は指定 revision の9ファイルだけを取得する。
各ファイルを公開する前に記録済みサイズ・SHA-256 を検査し、最終ディレクトリ全体も元の
manifest と一致することを要求する。既存の未知のファイルを保護し、安全でない redirect を拒否し、
TLS・checksum 検証は無効化しない。中断後は検証済みファイルを再利用できるが、
未検証の partial ファイルはモデル入力にしない。proxy の失敗だけで Hugging Face の認証不足とは判断しない。

## CPU canary と時間計測

```bash
.venv/bin/python scripts/t22_kv_cpu_canary_v0.py run \
  --model-path /workspace/models/llama32_3b_bf16_t21 \
  --output runs/t22_cpu_timing_v0 --items 1 --threads 4
```

時間計測対象は元の露出済み canary の項目0に固定し、結果で選択しない。
同一 CPU モデルで標準 eager attention、過去の adapter、新 T22 adapter を比較する。
元の88行配置（両 anchor・両 distance・2 donor・全11条件）で旧新の最終状態・neutral 状態の
完全一致と、同一 slot no-op・roundtrip の完全一致を要求する。
4操作の絵文字位置・suffix 比較は、anchor 21・distance 8 の別の16行 batch で取得し、
同一 slot の neutral companion を用意する。実際の注意重みと mass 診断を保存する。

この実装・時間確認の後に、別の出力ディレクトリで露出済み8項目すべてを実行する。

```bash
.venv/bin/python scripts/t22_kv_cpu_canary_v0.py run \
  --model-path /workspace/models/llama32_3b_bf16_t21 \
  --output runs/t22_cpu_canary_v0 --items 8 --threads 4
```

項目ごとの chunk は hash に結び付け、完了出力は変更しない。
`--resume` は同じ仕様の未完了 run にだけ使用する。
完了済みの1項目計測を8項目 run として再開しない。
全体の費用を推定する前に stage 別の実測時間と peak RSS を報告する。
効果の符号で実装検証の継続を判断しない。解釈に進む前に runtime と adapter の一致を確認する。

この経路は **CPU 上の実装検証証拠を再取得**する。
元の配列と互換 runtime なしに、RTX 5090 出力との bit-exact 一致は示せない。
語彙効果も算出しない。その段階には固定128 source の alias gallery 全体と target alias baseline を
CPU で再取得する必要がある。別 gallery への置換、8項目の確認実験への昇格、
過去 GPU gate の緩和はしない。384項目の K/V 探索は後続の独立した仕様固定・取得とする。

## 検証範囲

リポジトリ直下から、未使用の出力パスを指定してソースに結び付けた全体検証を再現する。

```bash
.venv/bin/python scripts/validate_t22_cpu_engineering_v0.py \
  --output /tmp/t22-cpu-synthetic-validation.json
```

現在の環境での結果は
[`synthetic_validation.json`](../validation/t22_cpu_engineering_v0/synthetic_validation.json)
に保存する。

downloader はネットワーク・モデルにアクセスしない byte-stream テストで整合性を検証する。
CPU runner はランダム小型モデルで、元の batch 配置と出力・再開時の provenance を検証する。
小型モデルの時間を3B checkpoint の時間とは扱わない。
実 checkpoint の load と固定1項目の時間計測は成功した。Pilot の acquisition receipt SHA-256 は
`c49a18f5a756bf5dc4c2cc4056776ac25bf6cba1a7d8ef7a22aeb7027bd0f120`。
独立監査ではモデル9ファイルすべての hash を再計算し、保存済み34配列を検査した。
[監査 receipt](../validation/t22_cpu_engineering_v0/timing_independent_validation.json) に記録する。
8項目 CPU canary と独立監査は **2026年10月20日05:06（日本時間）に成功して完了した**。
8項目それぞれで9つの実装検査がすべて成功し、監査では保存済み272配列を再検査した。
取得時の model forward は240回（sequence forward は6,288回）、nonreadout attention の
検査は576回。Canary は3 token の glyph 6項目、2 token の glyph 2項目で構成され、
効果による選択・除外はしていない。

保存した証拠：

- [取得 receipt](../validation/t22_cpu_engineering_v0/canary_acquisition_receipt.json)、
  SHA-256 `27c9e58535a872861a87c22d7b82dce7f9e54952bc229511b7231a9693dca901`。
- [独立監査](../validation/t22_cpu_engineering_v0/canary_independent_validation.json)、
  SHA-256 `d6a73eea7845e47fe373b259ab1cb472a7cd3452f2519290a44fc84e93c5b952`。
- [凍結仕様](../validation/t22_cpu_engineering_v0/canary_specification.json) と、
  `validation/t22_cpu_engineering_v0/canary_item_receipts/` の変更していない項目別 receipt。

これらは生成済み証拠の byte 単位で同一なコピーで、raw 配列は
`runs/t22_cpu_canary_v0/` に保持する。Supervisor の status は `complete`。
完了の記録時に supervisor から監査・取得・項目 receipt・raw NPZ までの hash を再照合した。
8項目の独立監査ではモデルファイルの hash を別途再計算していないが、取得処理が run 前後に検証し、
先行1項目の独立監査で全9ファイルを再計算している。

これで実装検証は完了した。この段階では語彙効果・過去 GPU 出力との一致・意味や機構の結論は
未確立だった。その後、同一 CPU runtime で固定128 source の alias gallery と target alias を
取得し、別段階の記述的な[語彙結果](T22_CPU_LEXICAL_RESULTS_V0.ja.md)を得た。
過去 GPU 出力との一致・意味や機構の結論は引き続き未確立。

run 完了後、保存配列と provenance を独立に監査する。

```bash
.venv/bin/python scripts/validate_t22_cpu_acquisition_v0.py \
  --run runs/t22_cpu_timing_v0 --expected-items 1 \
  --model-path /workspace/models/llama32_3b_bf16_t21 \
  --output /tmp/t22-cpu-timing-independent-NEW.json
```

独立監査は取得 runner や Torch を import せず、NumPy を使う。
各項目の全34配列、保存 readout の一致、local V-only attention の一致、配置、
mass の完全な再構成を再検査する。Full hidden tensor、stock/idle の比較対、
donor capture の比較対、nonreadout attention 出力はすべてが保存されているわけではない。
そのため、それらの全状態の assertion は独立再検査ではなく、ソースに結び付けた取得時の検査として残る。

## 長時間 run の管理

現在の supervisor は、完了した1項目計測を独立検査し、変更していない8項目 CPU protocol を実行し、
その完了後に独立監査する。Subprocess の失敗や結び付けたソースの変更で停止する。
Log と atomic な status 更新は `runs/t22_cpu_orchestration_v0/`、
取得結果は `runs/t22_cpu_canary_v0/` に保存する。`status.json` と、その `active_log` を確認する。
`status=complete` と最終監査の成功が揃って初めて完了とする。

未使用の出力・state ディレクトリを使う場合の管理コマンド：

```bash
.venv/bin/python -u scripts/run_t22_cpu_canary_after_timing_v0.py \
  --model-path /workspace/models/llama32_3b_bf16_t21 \
  --timing-run runs/t22_cpu_timing_v0 \
  --canary-run runs/t22_cpu_canary_NEW \
  --state-dir runs/t22_cpu_orchestration_NEW
```

Supervisor または取得 process が動いている間は重複起動しない。
進行中の時間計測を監視する場合、任意引数 `--timing-pid` と `--timing-start-ticks` は
両方を指定する。両方を省略した場合、処理開始前に完了済みの時間計測 receipt を要求する。
Supervisor は1項目 run を拡張せず、その配列を8項目の receipt として再利用しない。

環境 snapshot から machine を再起動しても、live process の復元は保証されない。
取得が動いていないと確認した後、同一仕様で未完了の8項目 run だけを元の runner の
`--resume` で再開し、その後、独立 validator を `--expected-items 8` と新しい report 名で実行する。
完了済み run は変更しない。起動手順にはこの復旧経路を残し、2つ目の長時間 run を暗黙に起動しない。
