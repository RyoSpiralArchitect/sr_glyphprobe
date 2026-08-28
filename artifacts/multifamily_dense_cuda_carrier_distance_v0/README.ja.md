# 公開証拠: multifamily dense CUDA carrier-distance v0

[English](README.md) · [結果](../../docs/MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.ja.md) · [固定プロトコル](../../docs/MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0.ja.md)

このdirectoryには、T6 model forwardより前にcommit
`5e2f4984486b5e5dc87b93f656d6e00bc8718baa`でprospective freezeしたprotocol
`glyphprobe-multifamily-dense-cuda-carrier-distance-v0`の完全なcompact evidenceを
収録している。

事前登録outcomeは`no_dense_model_distance_attenuation`である。4つのmodel-level
intersection-union testは、いずれもHolm補正後に棄却されなかった。Mistral 7Bでは強い
距離1 recurrence成分が得られたが、固定した正のlog距離減衰成分を通過しなかった。

## 内容

- `runs/`: Gemma 2 2B IT、Gemma 3 4B IT、Mistral 7B Instruct v0.3、Gemma 3
  12B ITの完全なactivation array、順序付きobservation、receipt、内部ledger。
- `analysis/`: 160個すべてのcarrier×距離×深度row、joint receipt、report、ledger。
- `TRANSFER_RECEIPT.json`: 凍結sourceの転送、自然なlifecycle開始gate、炉からmac2への
  返送、byte検証の境界。
- `PUBLIC_MANIFEST.json`: 公開payloadの正確なbyte数とSHA-256。

Repository rootから、次のコマンドで整合性を再検証できる。

```bash
python scripts/multifamily_dense_cuda_carrier_distance_v0.py validate-run \
  artifacts/multifamily_dense_cuda_carrier_distance_v0/runs/gemma2_2b_it
python scripts/multifamily_dense_cuda_carrier_distance_v0.py validate-run \
  artifacts/multifamily_dense_cuda_carrier_distance_v0/runs/gemma3_4b_it
python scripts/multifamily_dense_cuda_carrier_distance_v0.py validate-run \
  artifacts/multifamily_dense_cuda_carrier_distance_v0/runs/mistral7b_instruct_v03
python scripts/multifamily_dense_cuda_carrier_distance_v0.py validate-run \
  artifacts/multifamily_dense_cuda_carrier_distance_v0/runs/gemma3_12b_it
python scripts/multifamily_dense_cuda_carrier_distance_v0.py validate-analysis \
  artifacts/multifamily_dense_cuda_carrier_distance_v0/analysis
```

検証合格が示すのはbyte整合性とprotocol適合だけである。単調減衰、持続時間、意味、
因果機構、tokenizerの同等性や因果性、backendやnodeの同等性、model-scale・precision効果、
確認、Phase I gateのclosureは示さない。
