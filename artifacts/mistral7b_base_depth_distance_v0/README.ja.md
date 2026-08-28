# 公開証拠: Mistral 7B base depth-by-distance v0

[English](README.md) · [結果](../../docs/MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.ja.md) · [固定protocol](../../docs/MISTRAL7B_BASE_DEPTH_DISTANCE_V0.ja.md)

このdirectoryには、T7 model forwardより前にcommit
`25de47a5fb4c9eaf7674d5b2fa49f0c2cf84ca8b`でprospective freezeしたprotocol
`glyphprobe-mistral7b-base-depth-distance-v0`の完全なcompact evidenceを収録する。

登録済みoutcomeは`recurrence_and_early_depth_attenuation_excess`である。固定した両成分が
19,999 drawのpermutation下限に達し、1 modelのIUTは棄却された。ただしT6後に選んだ
cellであり、独立確認でもinstruction tuning効果のtestでもない。

## 内容

- `runs/mistral7b_base_v03/`: 完全なactivation array、順序付きobservation、run receipt、
  内部ledger。
- `analysis/`: 40件すべてのcarrier × distance × depth row、analysis receipt、report、ledger。
- `TRANSFER_RECEIPT.json`: model download、freeze転送、実行開始、結果返送、resource解放の境界。
- `PUBLIC_MANIFEST.json`: 公開payloadの正確なbyte数とSHA-256。

Repository rootから次のように整合性を再検証できる。

```bash
python scripts/mistral7b_base_depth_distance_v0.py validate-run \
  artifacts/mistral7b_base_depth_distance_v0/runs/mistral7b_base_v03
python scripts/mistral7b_base_depth_distance_v0.py validate-analysis \
  artifacts/mistral7b_base_depth_distance_v0/analysis
```

検証合格が示すのはbyte整合性とprotocol適合だけである。意味、機構、因果、
instruction-tuning不変性、checkpoint同等性、model一般性、確認、Phase I gate完了は示さない。
