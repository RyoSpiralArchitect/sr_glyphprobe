# E2 Llama 3.2 3B MPS絵文字transport v1 preflight failure

[English](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.md) · [凍結済みv1プロトコル](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1.ja.md) · [機械可読receipt](../validation/llama32_3b_mps_emoji_transport_v1/preflight_failure_receipt.json)

## 状態

E2 MPS transport v1は、model forwardを伴わないtokenizer preflightで停止した。
Language modelのweightは読み込まず、model forwardは0回で、launcherもrun namespaceも
作っていない。科学的outcomeは存在しない。V1は実行前に廃止し、同じversionのまま
修復やresumeをしてはならない。

Static freeze commitは
`a6803c7b673404b2bae4200cebe802b79cbc5782`である。Preflightは次のerrorで停止した。

```text
Emoji token offset crosses wrapper text for w01_mark_anchor/sky_slot_00
```

## 原因

該当profileのraw glyphは、token ID `[9468, 234, 239]`になる。一方、source wrapper内では、
直前のspaceと絵文字の先頭成分がcontextual token `11410`を作り、
`[11410, 234, 239]`となる。絵文字の文字区間は`(6, 7)`だが、先頭tokenのoffsetは
`(5, 7)`である。凍結済みv1 auditは、絵文字と重なるcontextual tokenのoffsetとIDが
raw glyphと一致することを誤って要求していた。

これはpreflight仕様の不備であり、modelの結果ではない。公開済みのwrapper/panel全体を
tokenizerだけで診断すると、contextual first tokenは、7 wrapperで`9468`、9 wrapperで
`11410`という2つの固定profileに分かれた。それでも16 wrapperすべてで、35-item core armは
一定の3-token spanを保ち、想定したfamily-middleとmatched-slot suffix構造、wrapper内で
一定のpositionとtoken数、変化しないoutside-token列を満たした。この診断は新しいauditを
設計する根拠にはなるが、v1を後から合格扱いにはしない。

## 処置

V2 studyでは、protocol ID、manifest、config、preflight receipt、run name、validation receipt、
analysis出力先、公開bundleを新しくする。Preflightでは、次の項目を分けて固定する。

- raw glyphの正確なtoken ID
- wrapperごとの正確なcontextual first-tokenとoffset profile
- `[wrapper_first, family_middle, slot_suffix]`というcontextual core pattern
- wrapper内で一定のposition、token数、anchor、outside-token列

科学panel、model、layer、strength、target、wrapper、bootstrap、primary endpoint、主張境界を
変えない場合でも、model forward前にv2として改めてhash固定する。V1は、絵文字transportを
支持する証拠にも反証する証拠にもならない。
