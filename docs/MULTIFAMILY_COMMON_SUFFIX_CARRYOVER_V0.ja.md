# Multifamily common-suffix carryover v0

[English](MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0.md) · [T3プロトコル](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0.ja.md) · [T3結果](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.ja.md) · [研究ロードマップ](ROADMAP.ja.md)

Protocol ID: `glyphprobe-multifamily-common-suffix-carryover-v0`

## 状態と、今回だけで問うこと

これは、探索的な観測結果を反証にかけるための事前プロトコルです。英日2文書、
設定、実行・解析コード、テスト、engineering preflight、checksum manifestを含む
最初の公開commitをもって、実行可能なfreezeとします。そのcommitより前に、
このprotocolのactivation結果を見てはいけません。

T3では、生の絵文字を構成する最後のtoken位置で`resid_post`を読みました。固定した
matched-slot nullはOLMoで棄却され、Gemmaでは棄却されませんでした。しかしOLMoでは、
同じslotにある絵文字が末尾tokenそのものを共有します。この事実だけでT3の局所的な
再現を十分に説明できるため、意味や因果を示す結果ではありません。

今回は、読み出し位置を厳密に1 token後ろへ移します。50個すべてで同一となる共通の
接尾token上でも、固定した10-slot構造を検出できるかを問います。残れば、この測定条件
における「1 token先までの文脈的な持ち越し」の証拠になります。消えれば、検査した
深度におけるT3の再現を、生の絵文字またはそのtoken位置に局在させる証拠になります。
どちらの場合も、絵文字の意味を検証したことにはなりません。

## 固定入力と2つの接尾文脈

T3のpanelを変更せず再利用します。sky、food、animals、transport、socialの順に、
連続する10 code pointからなる5 familyを並べ、各familyのslot 0〜9を揃えます。
絵文字、family、slotの追加・削除・並べ替えは行いません。

各絵文字を、事前に定めた次の2文脈へ入れます。

| 文脈 | 厳密な入力 | Gemmaの接尾token | OLMoの接尾token |
|---|---|---:|---:|
| `period` | `絵文字 + "."` | 235265 | 13 |
| `newline` | `絵文字 + "\n"` | 108 | 198 |

この2文脈はactivationを取得する前に選びました。一種類の句読点だけに結果が左右
されるのを避けるためであり、互いに独立した追試として数えるものではありません。

model forwardを一度も行わないtokenizer-only preflightで、両model・両文脈の全50項目
について、次の条件を確認しました。

1. 文脈付き入力のtoken列は、生の絵文字のtoken列全体を厳密なprefixとして保つ。
2. その後ろに、文脈ごとに定めたtokenがちょうど1個だけ加わる。
3. 同じmodel・文脈では、その接尾tokenが50項目すべてで同一である。
4. 文脈付きの50 token列は、互いに異なる。
5. decodeすると、元の絵文字と接尾文字へ厳密に戻る。

したがって、Gemmaの入力は2 token、OLMoの入力は4 tokenです。ただし、生の絵文字に
対する両modelのtokenization条件は同じではありません。とくにOLMoでは、family tokenと
slot tokenが共通接尾tokenの直前に残ります。

## 固定するmodel cellとcapture

| Role | Artifactと実行node | 生の絵文字token | 読み出すtoken |
|---|---|---|---|
| `gemma2_2b_4bit` | 固定済み`mlx-community/gemma-2-2b-4bit`、mac2、MLX 4-bit | 互いに異なる50個のatomic token | 共通のperiodまたはnewline token |
| `olmo3_7b_bf16` | 固定済みlocal OLMo 3 7B、mac1、MLX BF16 | `[9468, family_token, slot_token]` | 共通のperiodまたはnewline token |

special tokenは加えません。各item×文脈について、`last_nonpad`、すなわち共通接尾token
位置の`resid_post`を、深度fraction `[0, 0.25, 0.5, 0.75, 1]`で取得します。解決式は
`min(num_layers - 1, floor(fraction * num_layers))`です。modelごとに100回forwardし、
各forwardから5本のactivation vectorを得ます。generation、intervention、保護した
targetへのアクセス、結果を見てからのlayer選択は行いません。

## 主endpointは一つだけ

文脈 (c)、深度 (\ell)、family (f)、matched slot (s)における共通接尾tokenの
activationを (h_{c,f,s,\ell}) とします。文脈×深度ごとにfamily平均を引き、残る平方和を
共有slot主効果とfamily×slot interactionへ分けます。

\[
T_{c,\ell} = \frac{SS_{\mathrm{slot},c,\ell}}
{SS_{\mathrm{slot},c,\ell}+SS_{\mathrm{interaction},c,\ell}}.
\]

model単位の主統計は、固定した2文脈×5深度、計10セルの (T_{c,\ell}) を同じ重みで
平均した値です。結果を見たあとで、都合のよい文脈や深度へ差し替えません。

nullでは、10個のslot labelをfamilyごとに独立して並べ替え、skyだけを固定します。
PCG64の各drawで得た残り4 familyの並べ替えを、10個すべての文脈×深度セルに共通して
使います。seedは`20260829`、drawは19,999回に固定し、

```text
p = (1 + count(T_randomized >= T_observed)) / 20,000
```

とします。2つのmodel-level p値を一つのfamilyとしてHolm補正し、familywise alphaは
0.05です。文脈別、深度別、文脈×深度別の値は副次的な記述として残しますが、個別の
判定には使いません。T3の生絵文字に対する統計は、固定済みの記述参照に限り、この
検定へ統合しません。

## 事前に定める結果の型

- **Dual-model common-suffix recurrence candidate:** 両modelの観測値−null平均が正で、
  両方がHolm補正後も棄却される。
- **Gemma-only common-suffix heterogeneity:** 正の差を伴ってGemmaだけが棄却される。
  model family、tokenizer、quantization、scale、nodeは切り分けられない。
- **OLMo-only common-suffix carryover:** 正の差を伴ってOLMoだけが棄却される。この測定
  条件では、matched-slot構造が1 token先の文脈まで残る。
- **Opposite null-centered direction:** 観測値−null平均の符号がmodel間で逆になる。
- **No common-suffix slot recurrence:** 上のどれにも当てはまらない。

どの型でも、両文脈、全深度、両model、負または混合の結果をすべて残します。都合のよい
subcellだけを主結果へ昇格させません。

## 主張できる範囲

共通接尾tokenで構造が残っても、観測結果であることは変わりません。直前の絵文字token
への局所attention、residual streamの力学、architecture、tokenizer設計、quantization、
scale、node、またはそれらの相互作用で説明できます。意味、因果機構、tokenizer非依存性、
model scale効果、backend parity、behavioral steeringは示せません。

また、これはtokenizationを完全に揃えた確認用control setではなく、Phase I論文gateを
閉じる実験でもありません。checksumとreplayのPASSが示すのは、integrityとprovenance
だけです。
