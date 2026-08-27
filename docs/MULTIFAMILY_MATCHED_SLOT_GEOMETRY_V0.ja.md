# Multifamily matched-slot geometry v0

[English](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0.md) · [E1の結果](EMOJI_FAMILY_EXPLORATORY_RESULTS.ja.md) · [Tokenizer census](MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.ja.md) · [研究ロードマップ](ROADMAP.ja.md)

Protocol ID: `glyphprobe-multifamily-matched-slot-geometry-v0`

## 状態と問い

これは探索的な観測実験の事前プロトコルです。英日2文書、設定、実行・解析
コード、テスト、engineering preflight、checksum manifestを含む最初の公開
commitをもって、実行可能なfreezeとします。そのcommitより前に、この
protocolのactivation結果を見てはいけません。先行するtokenizer-only調査は
model forward 0回であり、結果ではなく設計根拠として使います。

問うのは一つだけです。固定した5つの絵文字familyと10個の位置関係が、
tokenizer構造の大きく異なる2つのmodelで、固定した5深度にわたって再現する
でしょうか。絵文字の意味は検証しません。sky、food、animals、transport、
socialという意味カテゴリが内部に表現されているかを問う実験でもありません。

## 固定する5×10 panel

既存のE1 panelを、絵文字の追加や削除なしで再利用します。各familyは連続する
10個のUnicode code pointからなり、末尾の16進位置をfamily間で揃えています。

| Family | 固定code point | 絵文字 |
|---|---|---|
| sky | U+1F311–U+1F31A | 🌑 🌒 🌓 🌔 🌕 🌖 🌗 🌘 🌙 🌚 |
| food | U+1F351–U+1F35A | 🍑 🍒 🍓 🍔 🍕 🍖 🍗 🍘 🍙 🍚 |
| animals | U+1F411–U+1F41A | 🐑 🐒 🐓 🐔 🐕 🐖 🐗 🐘 🐙 🐚 |
| transport | U+1F691–U+1F69A | 🚑 🚒 🚓 🚔 🚕 🚖 🚗 🚘 🚙 🚚 |
| social | U+1F911–U+1F91A | 🤑 🤒 🤓 🤔 🤕 🤖 🤗 🤘 🤙 🤚 |

この共通位置を**matched slot**と呼びます。これはUnicode/tokenizer上の構成で
あり、意味ラベルではありません。

## 意図的に異なる2つのtokenizer条件

完了済みのcensusとtokenizer-only replayから、activationを取得する前に次の
条件を固定しました。

- Gemma 2では、50個すべてが互いに異なる1-tokenになります。family間で共有
  されるtoken位置はありません。
- OLMo 3では、全項目が厳密に3-tokenです。並びは
  `[9468, family_token, slot_token]`で、第2 tokenはfamily内で共通、第3 tokenは
  familyをまたいで同じslotなら共通です。50系列はすべて異なり、元の絵文字へ
  正確にdecodeできます。

この2条件は同等ではありません。OLMoでslot配置が再現しても、同一の末尾token
だけで説明できます。Gemmaで再現しても、学習済みtoken embedding、語彙設計、
Unicodeの規則性、architecture、quantization、またはそれらの相互作用が残り
ます。両方で再現した場合も、異なるtokenizer条件をまたぐ観測的な候補に限って
記述します。

## 固定model cellとcapture

| Role | Model artifact | Runtime | Token条件 |
|---|---|---|---|
| `gemma2_2b_4bit` | `mlx-community/gemma-2-2b-4bit` | mac2、MLX、4-bit | 互いに異なる50個のatomic token |
| `olmo3_7b_bf16` | sealed local OLMo 3 7B artifact | mac1、MLX、BF16 | prefix × family × slotの厳密なtoken分解 |

両modelは、local pathに依存しない全file manifestで固定します。special tokenを
加えず、絵文字1文字をそのままforwardし、最後のitem tokenの`resid_post`を
取得します。深度fractionは`[0, 0.25, 0.5, 0.75, 1]`で固定し、
`min(num_layers - 1, floor(fraction * num_layers))`で解決します。Gemmaでは
`[0, 6, 13, 19, 25]`、OLMoでは`[0, 8, 16, 24, 31]`です。

## 主endpoint：固定5深度のomnibus

ある深度で、family \(f\)、matched slot \(s\)のactivationを\(h_{f,s}\)とします。
まずfamilyごとの平均を引きます。残る平方和を、family間で共有されるslot主効果と
family×slot interactionに分け、

\[
T_\ell = \frac{SS_{\text{slot},\ell}}
{SS_{\text{slot},\ell}+SS_{\text{interaction},\ell}}
\]

を計算します。model単位の主統計は、固定した5深度の\(T_\ell\)を同じ重みで
平均した値です。結果を見たあとで、都合のよい深度に差し替えることはできません。

nullでは、10個のslot labelをfamilyごとに独立して並べ替えます。全familyを同時に
同じ順番へ並べ替えても対応関係は変わらないため、skyだけは固定します。残る4
familyはNumPy PCG64、seed `20260828`で19,999回並べ替え、各回の同じ並べ替えを
全深度に使います。

```text
p = (1 + count(T_randomized >= T_observed)) / 20,000
```

2つのmodel-level p値を一つのfamilyとしてHolm補正し、familywise alphaは0.05と
します。深度別の統計とp値はすべて残しますが、深度別の判定は行いません。

## 事前に定める結果の型

- **Dual-model slot-recurrence candidate:** 両modelの観測値がnull平均を上回り、
  両方のHolm補正後検定が棄却する。
- **Gemma-only heterogeneity:** atomic-token条件のGemmaだけが棄却する。
- **OLMo-only token-structured recurrence:** OLMoだけが棄却する。同じ末尾slot token
  を共有することを十分な説明として残す。
- **Opposite null-centered direction:** 観測値−null平均の符号がmodel間で逆になる。
- **No dual-model slot recurrence:** 上のどれにも当てはまらない。

どの型でも、全model、全family、全深度を残します。良好なlayerやfamily、別の
endpointをあとから主結果へ昇格させません。

## 副次出力と主張の境界

固定5深度のslot profile、slotを差し引いたfamily主効果、interaction比率、
activation RMS、全token系列、有限値check、実行時間とmemoryのprovenanceを残し
ます。時間は速度優位の主張には使いません。

この実験はintervention、generation、target bankへのアクセス、behavior評価、
因果検証を行いません。意味カテゴリ、tokenizer非依存のglyph特性、model scale、
quantization、node差、backend parity、確認的結論、Phase I論文gateの達成は示せ
ません。manifestとchecksumのPASSが示すのは、integrityとreplayabilityだけです。
