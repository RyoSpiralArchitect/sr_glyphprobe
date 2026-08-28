# 公開証拠: multifamily carrier-distance v0

[English](README.md) · [結果](../../docs/MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.ja.md) · [固定プロトコル](../../docs/MULTIFAMILY_CARRIER_DISTANCE_V0.ja.md)

このdirectoryには、commit `e0043c6af6a397ca229900fa5a0b4aa134d242b8`で
凍結したprotocol `glyphprobe-multifamily-carrier-distance-v0`の完全なcompact evidenceを
収録している。

事前登録outcomeは`no_model_distance_attenuation`である。Gemmaでは距離1の再現が
得られなかった。LlamaとOLMoでは距離1の再現が見られたが、固定した正のlog距離減衰成分を
通過しなかった。Holm補正後に棄却されたmodel-level intersection-union testはない。

## 内容

- `runs/`: Gemma、Llama、OLMoの完全なactivation array、順序付きobservation、receipt、
  内部ledger。
- `analysis/`: 120個すべてのcarrier×距離×深度row、joint receipt、report、ledger。
- `TRANSFER_RECEIPT.json`: mac1、炉の中継点、mac2における凍結packageとOLMo返送物の
  byte一致。炉のGPU計算は使っていない。
- `PUBLIC_MANIFEST.json`: 公開payloadの正確なbyte数とSHA-256。

Repository rootから、次のコマンドで整合性を再検証できる。

```bash
python scripts/multifamily_carrier_distance_v0.py validate-run \
  artifacts/multifamily_carrier_distance_v0/runs/gemma2_2b_4bit
python scripts/multifamily_carrier_distance_v0.py validate-run \
  artifacts/multifamily_carrier_distance_v0/runs/llama32_3b_bf16
python scripts/multifamily_carrier_distance_v0.py validate-run \
  artifacts/multifamily_carrier_distance_v0/runs/olmo3_7b_bf16
python scripts/multifamily_carrier_distance_v0.py validate-analysis \
  artifacts/multifamily_carrier_distance_v0/analysis
```

検証合格が示すのはbyte整合性とprotocol適合だけである。単調減衰、持続時間、意味、因果機構、
tokenizer非依存性、backendやnodeの同等性、確認、Phase I gateのclosureは示さない。
