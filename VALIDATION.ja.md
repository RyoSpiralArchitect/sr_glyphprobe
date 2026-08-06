# GlyphProbe v1 検証結果

[English](VALIDATION.md)

## 公開版の test suite

現行の公開環境で **76 テストすべて**が完了した。対象は、厳密な config resolution/override、
validation receipt の相対 path 解決、capability boundary、MLX の receipt gate による activation patch 表明、
検証済み layer の強制、readiness input の fail-closed 判定、public bundle の path/receipt 相互照合、
packaged resource、direction 構築と control、fingerprint statistics、Transformers/TransformerLens hook adapter、
metric/factor identity、readiness の拒否経路、sealed mock の実行/resume、surface-server の resume 振る舞いである。

決定論的 mock smoke receipt には、1,314 件の intervention/control record、0 error、完全な zero-hook no-op、
resume 後も不変の record 数が記録されている。readiness は 9/11 である。この小さな smoke は意図的に、
必要な target 数と 3 段階 dose grid を省いている。mock 出力は plumbing の証拠でしかない。

## Live MLX バックエンド検証

`validation/mlx_gpt2_parity/receipt.json` の SHA-256 固定 receipt は、次の 1 セルに限り
`validated_mlx_selected` の status を持つ。

- `openai-community/gpt2`、revision
  `607a30d783dfa663caf39e06633721c8d4cfcd7e`
- FP32 `resid_post`、介入層 2、4、7、9
- 長さの異なる 4 つの固定 prompt
- Transformers/MPS を reference、MLX Metal を candidate とする比較

正確な token ID、baseline/介入後の logits/activation、zero-hook no-op、argmax 一致、intervention fidelity、
差分の方向と magnitude を含む **80/80 の parity gate** がすべて通過した。記録された同期 end-to-end benchmark の
総合 median は、Transformers/MPS が 17.517 ms、MLX が 10.727 ms で、**1.633× の高速化**だった。receipt の SHA-256 は次の通り。

```text
98c3873a1ec6166aeae0fbb5d9abcd587eb1b3996726912ab963ff35ee497679
```

絶対 latency は実行時負荷の影響を受けるが、固定した比較は相対 speed gate に合格した。これは 1 台のマシンと
1 つの workload におけるバックエンド選択の結果である。一般的な MLX 速度の主張や glyph に関する証拠ではない。
他の model、revision、dtype、site、hardware、prompt 分布、量子化 variant は未検証セルのままである。

## 標準 MLX 行列

固定した parity receipt と現行 source に結び付いた完了済み行列は次の通り。

```text
colored-shapes-v1-standard-mlx--mlx--openai-community-gpt2--c493ae1e18743922
```

この run は 254.633 秒で完了し、14,208 件の intervention/control record、0 error、事前因果 readiness 11/11、
zero-hook の activation/logit RMS 差分 0、`causal_claim_authorized: false` を記録した。artifact audit は 15/15 を通過し、
status は `ready_with_caveats` だった。

```text
validation/run_audits/colored-shapes-v1-standard-mlx--c493ae1e18743922.json
```

強化した run seal は、config/data hash、固定 parity receipt、install 済み source、dependency/runtime identity、
loaded model の path 非依存 artifact manifest を結び付ける。run directory の選択前にバックエンドを load するため、
runtime または model manifest が変わると、既存 record を新しい receipt の下で密かに resume する代わりに、別の run ID になる。

## 必須の解釈限界

- 14,208 record の全 pipeline は MLX だけで実行した。PyTorch/MPS parity は固定 prompt/layer/vector に対するもので、
  全行列を重複実行したものではない。
- Fingerprint advantage はセル間で異質で、非正のセルも含む。最大行だけではなく、分布、median、cross-seed aggregate を報告する。
- primary glyph の token 数は揃っているが、token identity は同じではない。neutral glyph は 1 token、primary glyph は 3 token である。
- permutation p 値は有限の `1/1001` floor を持つ screening flag で、多重性補正済み global significance test ではない。
- source seed は反復した direction estimate で、独立観測ではない。主な sampling cluster は target prompt である。
- Iso-KL、SAE、generation、`resid_pre`、`attn_out`、`mlp_out`、path-level causal test は実行していない。

完了済みの結果は、再現可能な事前因果 fingerprint candidate であり、限定的な後続実験の足場である。
glyph の意味、circuit、causal path を特定したものではない。
