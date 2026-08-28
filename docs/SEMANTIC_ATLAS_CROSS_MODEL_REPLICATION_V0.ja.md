# Semantic Atlas モデル横断再現 v0（T10）

状態：**9セルのengineering preflight完了済み・取得前protocol**。292項目を使ったT10候補モデルのforwardは、まだ一度も実行していない。

英語版：[SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.md](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.md)

## 問い

T9では、Mistral-7B baseの一つのcheckpointにおいて、搬送条件を変えても崩れないitem retrieval差が確認された。すなわち、glyph表現から対応するUnicode公式名を検索したときの精度は、`U+...` リテラルを対照にした検索精度を、固定済みの8 carrier-distanceセルすべてで上回った。

T10で問うのは、次の一点に限る。

> 各モデルでトークン数を厳密に揃えた対照も必須としたとき、凍結済みの4コアmodel/tokenizerセルのうち、3セル以上でitem-name alignmentが再現するか。

対象はあくまで、Unicode公式名との**項目対応**である。肯定結果が出ても、絵文字の「意味」を理解している、tokenizerに依存しない、どのarchitectureにも普遍的に成り立つ、といった主張はできない。

## endpointを二つ記録する理由

T8/T9ではlayer 31の取得点を `resid_post` と呼んでいたが、実装が選んでいたのは `output.hidden_states[layer + 1]` だった。2層の小さなMistralを使った合成監査では、最終層におけるこの値はrawな最終decoder block出力ではなく、model最終normを通過したhidden stateだった。実際、`model.model.norm(last_block_output)` と完全一致し、raw出力とは異なった。

そこでT10では、同じforwardから二つのendpointを記録する。

| endpoint | 取得方法 | 役割 |
|---|---|---|
| `returned_final_hidden_state` | `output.hidden_states[-1]` | 唯一の判定対象。T9とAPIレベルで同一 |
| `raw_last_decoder_block_output` | 最終decoder blockのforward hook | 登録済み副次。一次結果の救済には使えない |

これはT9の数値を読み替えるものではなく、表現の呼び方を正すための整理である。T9の凍結済みファイルには手を加えず、そのまま監査可能な状態を保つ。

## 固定する項目と搬送条件

- 項目：T9と同じ292件。元のsource index順を維持する。
- view：raw glyph、Unicode公式名、`U+...` 形式のcodepointリテラル。
- carrier：各tokenizerで1 tokenになる `" a"` と `" |"` を、それぞれ8回反復。
- 読み出し距離：各viewの直後から1、2、4、8 carrier token先。
- batch size：forward 1回につき1系列。
- forward数：1モデル1,752回、9セル合計15,768回。
- 取得vector数：二つのendpointを合わせて1モデル14,016本、合計126,144本。
- 保存：8項目単位のatomic shard。activationはfloat32で保存し、GitとSpiralShareには置かない。

凍結前に、各tokenizerで次の条件をすべて検証する。

1. 3 viewとも292系列が空でなく、view内で重複しない。
2. carrierの単位文字列が、それぞれ正確に1 tokenになる。
3. carrierを8回付加しても、raw view側のtoken列が完全に保たれる。
4. 結合後のtoken列をdecodeすると、入力文字列を厳密に復元できる。
5. 後述するトークン数の完全一致層に、少なくとも250項目が含まれる。

## 凍結するmodel/tokenizerセル

選定根拠は、T10のactivationを見る前に確認できたimmutableな公開revision、または炉にすでに揃っていた完全artifactである。architecture、release、規模、instruction tuningの有無は混在しており、いずれの因子も単独では切り分けられない。

| role | artifact revision | parameter数 | 一次での役割 |
|---|---|---:|---|
| `llama32_3b_base_bf16` | `mlx-community/Llama-3.2-3B-bf16@60a99aaf...` | 3.21B | core |
| `qwen25_7b_base_bf16` | `Qwen/Qwen2.5-7B@d1497293...` | 7.62B | core、Qwen系列のanchor |
| `olmo2_1b_base_bf16` | `allenai/OLMo-2-0425-1B@a1847dff...` | 1.48B | core |
| `gemma2_2b_it_bf16` | `google/gemma-2-2b-it@299a8560...` | 2.61B | core、取得済みgated artifact |
| `qwen25_0p5b_base_bf16` | `Qwen/Qwen2.5-0.5B@060db649...` | 0.49B | 登録済み拡張 |
| `qwen25_1p5b_base_bf16` | `Qwen/Qwen2.5-1.5B@8faed761...` | 1.54B | 登録済み拡張 |
| `qwen25_3b_base_bf16` | `Qwen/Qwen2.5-3B@3aab1f19...` | 3.09B | 登録済み拡張 |
| `smollm2_1p7b_base_bf16` | `HuggingFaceTB/SmolLM2-1.7B@effd688a...` | 1.71B | 登録済み拡張 |
| `mistral7b_instruct_v03_bf16` | `mistralai/Mistral-7B-Instruct-v0.3@c170c708...` | 7.25B | 関連checkpoint拡張 |

Qwen 0.5/1.5/3/7Bの系列は記述目的に限る。scale law、単調性、model sizeの因果効果は主張しない。Mistral-Instructも、既知のMistral-base T9結果との記述比較に留める。baseとinstruction tuningの差だけを調べた対照実験ではない。

## forward前に確認したengineering preflight

9つのimmutable revisionはすべて、model weightを読み込まず、候補forwardも行わないstatic artifact/tokenizer gateを通過した。Artifact監査では、空でないweight fileが少なくとも一つあることに加え、すべての`*.index.json`の`weight_map`が参照するfileが実在することを要求する。この条件により、2本目のshardがまだ存在しなかったQwen 3Bの不完全snapshotを一度棄却した。同じrevisionの取得が完了した後にだけ、下表のreceiptを生成した。

| model cell | 存在するweight file / index参照file | 完全一致層の項目数 | 対象層数 | artifact manifest SHA-256 |
|---|---:|---:|---:|---|
| `llama32_3b_base_bf16` | 2 / 2 | 281 | 25 | `dc5b61a2c4aa...` |
| `qwen25_7b_base_bf16` | 4 / 4 | 284 | 22 | `bd8ef40517ce...` |
| `olmo2_1b_base_bf16` | 2 / 2 | 281 | 25 | `d92749838283...` |
| `gemma2_2b_it_bf16` | 2 / 2 | 284 | 16 | `1b2b83416e64...` |
| `qwen25_0p5b_base_bf16` | 1 / indexなし | 284 | 22 | `c860aa324659...` |
| `qwen25_1p5b_base_bf16` | 1 / indexなし | 284 | 22 | `cb56a7e1865b...` |
| `qwen25_3b_base_bf16` | 2 / 2 | 284 | 22 | `cca372c88da2...` |
| `smollm2_1p7b_base_bf16` | 1 / indexなし | 287 | 14 | `aaecf4014031...` |
| `mistral7b_instruct_v03_bf16` | 4 / 3 | 285 | 20 | `d20865c47632...` |

すべてのセルが、凍結した下限250項目を上回った。実測範囲は281〜287項目である。完全なhash、file数、byte数、token列、carrier境界、層構造は、9件のJSON receiptに残す。

## モデルごとの一次判定：二つの条件を両方通す

carrier-distanceセルごとに3 viewの行列を別々に中心化し、各行をL2正規化する。forward retrieval差は、次の通り。

```text
Top-1(glyph -> 対応するUnicode公式名)
  - Top-1(glyph -> 対応するU+リテラル)
```

8セルのうち最小の差を、搬送条件に頑健な統計量とする。各モデルでは、以下のAとBをどちらも満たさなければならない。

### A. 全292項目を使う成分

- queryとcandidateに292項目すべてを使う。
- 1回のrandomization drawでは、公式名の対応関係を8セル共通の一つの置換で崩す。
- codepointの対応と表現行列は固定する。

### B. トークン数を厳密に揃える成分

各項目を、次の完全一致keyで層別化する。

```text
(glyphのtoken数, 公式名のtoken数, codepointリテラルのtoken数)
```

1項目しかない層はBからだけ除外する。中心化、正規化、query、candidateはいずれも、残った項目集合の中で改めて計算する。公式名の対応は同じ層の内部だけで置換し、その層別置換を8セルで共通に使う。

AとBに共通する条件は次の通り。

- 19,999回の決定論的randomization。
- p値は `(1 + exceedances) / 20,000`。
- 実質差の下限は、8セル最小差が0.02以上。

モデル単位のp値は `max(p_A, p_B)` とする。IUT p値が0.05以下で、かつA・B双方の実質差が0.02以上の場合に限り、そのモデルは未補正の登録済みruleを通過する。一方の強い結果で、もう一方を補うことはできない。

## 唯一のモデル横断一次判定

4コアセルのIUT p値に対し、「少なくとも `r = 3` / `m = 4` セルで再現する」というBonferroni部分連言検定を行う。

```text
p_PC = min(1, (m - r + 1) * p_(r)) = min(1, 2 * p_(3))
```

`p_(3)` は、コア4セルのうち3番目に小さいIUT p値である。肯定には、次の二条件を両方要求する。

1. `p_PC <= 0.05`
2. A・B双方の実質差を通過したコアセルが3つ以上

肯定時に許される表現は、次の範囲に限る。

> 凍結済みの4コアmodel/tokenizerセルのうち、少なくとも3セルで、登録済みruleに基づく再現が得られた。

9セルのIUT p値については、個別セルを限定して報告するためのHolm familyも別に置く。この個別判定は副次であり、部分連言検定に失敗した一次結果を救済できない。

## 登録済み副次出力

- raw最終block endpointとreturned stateとの差。
- Qwen 4点の規模profile。
- 全carrier・distanceにおけるTop-1、MRR、cosine margin、centered linear CKA。
- token数histogramと完全一致層のcoverage。
- model別のlatency、peak memory、artifact size。
- 既知のMistral-base T9結果との記述比較。

副次結果を見てからmodel、endpoint、項目、carrier、distance、threshold、seed、層別規則を選び直すことは禁止する。

## 結果ごとの着地点

### 分岐1：モデル横断一次判定を通過

部分連言p値、実質差を通過したコアセル数、Holmを通過した個別セルを、そのまま報告する。次の因果実験に進めるのは、トークン数を揃えた成分まで通過したセルだけである。主張対象は引き続きUnicode公式名とのitem alignmentに限る。

### 分岐2：一部の個別セルだけ通過

Holmを通過したセルを限定的に報告し、モデル横断一次は不成立と明記する。次に調べるべき対象はarchitecture/tokenizer間のheterogeneityであり、成功セルから一般化は行わない。

### 分岐3：全項目では通るが、トークン数一致では失敗

tokenization structureを有力な説明として残す。これは有用な負の結果であり、alignment差を因果的に解釈する道をいったん閉じる。

### 分岐4：どちらも再現しない

T9をMistral-base固有の限定結果として扱う。T11で変わったglyphを探索することはできるが、T10で得られなかったモデル横断のsemantic premiseを持ち込まない。

## 凍結と実行のゲート

候補モデルを初めてforwardする前に、commit済みfreezeへ次を束ねる。

- 本文書と英語版、実装、合成test。
- T9のsource receipt 5点とSHA-256。
- endpoint semanticsの合成監査。
- 9モデルのartifact manifestとtokenizer token列receipt。
- joint engineering preflight、一次rule、seed、threshold、model roster。

実行は1モデルずつ行う。model load前と8項目shardごとに炉の競合を確認し、他processが現れたらyieldする。完了shardは再取得せず、不完全なstaging directoryがあればfail closedとする。model別summaryでは二つのendpointを計算するが、joint randomizationの判定対象は凍結済みの一次endpointだけである。

## 主張できないこと

最も強い肯定結果でも、次は示せない。

- 人間的・合成的な絵文字の意味。
- tokenizer非依存性。
- 独立した再現実験。
- 因果回路やmechanism。
- behavior、steering、generationへの効果。
- baseとinstruction tuningの効果差。
- scale lawや規模に対する単調変化。
- architecture全体、または全モデルへの一般化。
- Phase I論文gateの完了。

T10の役割は、単一checkpointで確認した結果を、境界の明確なモデル横断セル結果へ進めることにある。絵文字意味の分解は、その先で検証する仮説であって、T10の結論ではない。
