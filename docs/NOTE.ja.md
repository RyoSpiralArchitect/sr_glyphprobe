# 絵文字は、モデルの中に同じ跡を残すのか

[Mistral base深度×距離結果](MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.ja.md)

[English](NOTE.md) · [Dense CUDA結果](MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.ja.md) · [Carrier-distance結果](MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.ja.md) · [Common-suffix結果](MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.ja.md) · [Matched-slot geometry結果](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.ja.md) · [Multifamily geometry結果](MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.ja.md) · [Tokenizer census結果](MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.ja.md) · [E2 MPS transport v2プロトコル](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.ja.md) · [v1 preflight failure](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.ja.md) · [holdout状態](HOLDOUT_STATUS.ja.md) · [E2 Stage A3数値screen結果](LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.ja.md) · [E2 Stage A v2結果](LLAMA32_3B_MLX_VALIDATION_RESULTS.ja.md) · [E1 探索結果](EMOJI_FAMILY_EXPLORATORY_RESULTS.ja.md) · [Milestone 2 結果](MILESTONE2_RESULTS.ja.md) · [研究ロードマップ](ROADMAP.ja.md)

絵文字を言語モデルに見せたとき、内部では何が起きているのだろう。

つい「青い丸には、青や丸の意味が埋め込まれているのではないか」と考えたくなる。けれど、その問いは最初の一歩としては大きすぎる。モデルの内部に意味を見つけたつもりになる前に、もっと地味で、もっと厳しい確認が要る。同じ絵文字から作った方向は、条件を変えても同じような出力差を残すのか。単なるランダム方向より、本当にまとまって見えるのか。

GlyphProbe は、その順序を守るために作った。

## まず、意味ではなく「跡」を測る

今回使ったのは、5色と2つの形を組み合わせた10個の絵文字だ。

```text
🟤 🟫   🟠 🟧   🟢 🟩   🔵 🟦   🟣 🟪
```

それぞれを16種類の短い文脈に入れ、モデル内部の活性化から方向を作る。その方向を別の24プロンプトへ少しだけ足し、次トークンの全ロジットがどう動いたかを記録する。介入の大きさ、クリッピング、ターゲット、ランダム方向、ゼロ介入は、すべて同じ計画に封じた。

ここで見ているのは、出力差分の「向き」だ。同じ絵文字なら、異なるターゲットでも似た差分を残すか。ソース文の一部を入れ替えて方向を作り直しても、その傾向は残るか。これを、同じノルムのランダム方向と比べる。

意味の解釈は、まだしない。まずは跡が繰り返すかどうかだけを見る。

## MLX は、速さより先に同じものを測れているか確かめた

Apple silicon では MLX が速そうだった。ただ、実験基盤を変えると、同じモデル名でも同じ数値を測っているとは限らない。トークナイザー、重みの読み込み方、演算の融合、dtypeが少し違うだけで、結果は動く。

そこで GPT-2 のリビジョンを固定し、FP32、`resid_post`、レイヤー2・4・7・9に範囲を絞った。4種類のプロンプト長と4レイヤーを組み合わせ、トークン列、基準ロジット、活性化、ゼロ介入、固定した非ゼロ介入を Transformers/MPS と照合した。

結果は80項目中80項目が合格。記録時のエンドツーエンド中央値は 17.517 ms から 10.727 ms へ縮まり、MLX は1.633倍だった。だから今回は MLX を使った。速かったからではなく、固定した範囲で同じ測定だと確認したうえで、速かったからだ。絶対時間は、そのときのマシン負荷にも左右される。

もちろん、このレシートは万能ではない。別のモデル、量子化、別の介入点に持ち出した瞬間、検証はやり直しになる。

後続runには、速度の境界が必要な理由を示す記録も残った。Matched-null Aの最初のforeground processは、マシン負荷が極端に高い最中、798行で外部から中断された。Median latencyはbaselineの10.73 msではなく約309 msだった。Sealを保ったresumeによって、重複・欠損・error・非ゼロのzero-hook RMSなしで14,208行の正確なgridを完了した。その後のlatencyは約12.43 msへ戻った。これは運用上の来歴であり、モデルに関する証拠でも、一般化できる速度の結果でもない。P2、独立ソース、診断runは通常どおり完了した。

## 最初の地図には、輪郭とむらが同時に出た

標準実験では14,208件の介入を MLX で走らせ、エラーは0件だった。この全パイプラインを Transformers/MPS でも重ねて実行したわけではない。ゼロ方向を足した96条件では、活性化もロジットも変わらなかった。要求した介入量と実測値も、数値誤差の範囲で一致した。

出力指紋のランダム方向に対する優位量は、36セルの中央値で0.6075。別々に作ったソース方向をまたぐ集約では0.9308だった。方向の作り直しに対する一致度、用量反応、符号反転も、次の因果実験へ進む内部基準を満たした。

でも、きれいな成功譚にはならない。

36セルのうち、優位量が正だったのは25セル。残る11セルはゼロ以下だった。レイヤーごとの中央値はすべて正でも、個々の条件では向きが反転する。最大値だけを取り出せば、とても強い効果に見える。けれど、それでは地図の凹凸を消してしまう。今回の中心は、最大セルではなく全体の中央値と、シードをまたいだ集約、そして11個の非正セルだ。

## 対照を入れると、地図の見え方が変わった

Milestone 2では、トークン化の警告の一部を、3つのnull panelで検査した。各panelは10条件で、すべての記号がGPT-2のraw tokenで3個、パネル単位の接頭構造も色付き図形と同じ9対1にそろえてある。ただし、token IDそのものを同じにはしていない。同一のtoken ID列は同一のbyte列へ戻るため、別glyphの対照にならないからだ。Panel Cには、意味的に近い対照として、参照パネルにない赤い四角`🟥`を事前申告のうえ1個だけ含めた。非色付き候補が、互いに重ならない27枠に対して1個足りなかったためである。

元の24ターゲットによる探索行列では、色付き図形scoreからpanel A/B/Cの中央値を引いた差が、36セルの中央値で`0.047427`だった。正は25セル、非正は11セル。保存済み96次元sketchを同じseedのまま48、32、24次元へ代数的に畳み込むと、`0.040200`、`0.028907`、`0.048591`だった。これは記述的な比較であって、独立した36観測でも、「何%を説明したか」という推定でも、CountSketchのseed感度でもない。

より重要なのは、凍結済み48件のP2バンクで得た結果だ。Layer 2の調整済みターゲット効果は`+0.208363`、凍結済みv1の95%区間は`[0.137463, 0.276893]`、Holm補正後は`p = 0.00143999`だった。別に用意した独立ソースラッパーでは`+0.187507`、`[0.125489, 0.247659]`、`p = 0.00393996`。どちらもv1規則で「指定済みmatched controlsに対して頑健」と判定された。

Layer 4は違った。主要ソースは`-0.0329465`、`[-0.0761085, 0.0110094]`。独立ソースは`-0.086379`、`[-0.159246, -0.016917]`。どちらも凍結済み規則では未解決だった。つまり、Milestone 2は全体として成功したのではない。レイヤーによって結果が分かれた。

## 結果を見たあとに、解析そのものも監査した

v1 analyzerは、凍結済みターゲット、モデルセル、条件grid、target単位の標本構造、仮説familyを検査する。ただし、primaryとnullの役割はコマンドライン引数の順序で決まる。そこで別のbinding auditを行い、公開した全14 run、すなわち探索・P2・独立ソースの中核12 armと診断2 runが、意図した凍結済みconfig、panel、source、target、path、hashへ正しく対応することを確かめた。この監査は合格している。

もうひとつ留保がある。v1の区間は、leave-one-group-out prototypeを一度作ってtarget効果を計算した後、その固定済み効果を再標本化している。Bootstrapの各replicateで、データ依存のprototypeを作り直してはいない。

事後感度分析では、すべてのprototypeを共同で作り直した。主要ソースの区間は、layer 2が`[0.099930, 0.295380]`、layer 4が`[-0.099995, 0.041902]`。独立ソースはそれぞれ`[0.104210, 0.271322]`と`[-0.185084, 0.007648]`だった。

区間は広がったが、この方法を決めたのはP2結果を見た後である。p値や確認的statusは付けず、v1判定も上書きしない。[技術的な結果](MILESTONE2_RESULTS.ja.md)では、この2つの推論層を分けて記録した。

トークン構造に関する2つの二次診断も完了した。どちらも14,208行を完走し、errorは0件、zero-hook RMSは0、readinessは11 / 11だった。Random-adjustedのheadline `emoji_fingerprint_advantage`は、末尾token一致panelが`+0.751225`、接頭構造均一化panelが`+0.601038`だった。このheadline値は、paired comparisonで使うraw separation scoreとは別の評価量である。

CountSketchの96、48、32、24次元で、standard-minus-suffix raw separationの中央値は、`+0.002624`、`+0.009473`、`+0.004026`、`+0.009700`。Standard-minus-prefixは、`+0.022096`、`+0.023254`、`+0.011040`、`+0.025387`だった。96次元で正だったのは、suffixが20 / 36セル、prefixが25 / 36セルである。これは事後的・記述的な診断であり、推論や同等性の検定ではない。低次元値は同じseedによる代数的な畳み込みで、独立した再実行でもseed感度でもない。

## Familyを差し替えると、共有部分が見えてきた

探索side trackのE1では、問いをさらに狭くした。10 glyphからなる5つの
familyを選び、対応するslotではGPT-2の第1・第3 tokenを共通にして、中間token
だけをfamilyごとに変えた。Token構造を強く統制できる一方、family identityと
中間tokenは切り分けられない。5本のMLX runより先に設計を凍結し、すでに
探索で使った24 targetだけを再利用した。E1はP2とC1のどちらも読み込んでいない。

Source familyとprototype familyを組み合わせた行列は、全体に正だった。
25 cellの平均値はlayer 2で`0.395455`〜`0.484915`、layer 4で
`0.602564`〜`0.681909`である。ところが、family内で上乗せされたglobalな
超過量はlayer 2で`0.014752595564`、layer 4で`0.014887989201`にとどまった。
Family別の記述区間はすべて0をまたいだ。Layer 4は想定したnegative
comparatorにならず、random controlを上回らないcellも30件中10件あった。

この結果から「GPT-2が5種類の意味上の絵文字familyを見つけた」とは言えない。
むしろ、matched-slot反復の多くは中間tokenを替えてもfamily間を移り、意図的に
共有した第1・第3 tokenが、小さく不均一なfamily固有成分より強く効いていると
読むのが妥当だ。[E1の全結果](EMOJI_FAMILY_EXPLORATORY_RESULTS.ja.md)には、
行列、区間、非正cellを省かず掲載している。p値や確認的statusは付けていない。

## 同じ絵文字でも、tokenizationの問題は同じではない

次のcontrol設計では、activationからいったん完全に離れた。固定censusで、mac1、mac2、
furnaceにすでにあった14 tokenizer artifactへ、固定文字列115件を4つの正確なtext
contextで入力した。Model forwardは行わず、target bankも開いていない。

14 artifactは、この有限surface上で7つの完全一致output classへまとまった。すべての
classでraw token数が同じだった文字列は6件だけである。Family ZWJ sequenceは、
compactなclassでは7 token、Mistral v0.3では20 tokenだった。先頭spaceの影響も大きく
異なり、ほぼ数が変わらないtokenizerがある一方、item-span countがMistralでは
115件中106件、Qwenでは98件変わった。

Blue circleとblue squareが、実務上の限界をはっきり示した。固定panelには、7 class
すべてでtoken数と先頭tokenを同時に揃える別itemが1件もなかった。Raw textでも、先頭に
spaceを置いても、固定promptの前でも同じだった。Byteに近い分割をするtokenizerでは
色・形のmatchが多数ある。一方、一部のGemma shapeは別々のatomic tokenなので、別glyphと
先頭tokenを共有する条件そのものが成立しない。

Controlが作れない、という結論ではない。Universal panelを単位にするのが不適切だった、
という結論である。将来のcross-tokenizer実験では、tokenizer構造ごとに実現可能な
control familyを別々にfreezeし、atomic-tokenの場合にprefix matchingを何へ置き換えるかも
先に宣言する。[Censusの全結果](MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.ja.md)は
記述的な設計証拠であり、新しいactivation結果でも論文gateでもない。

## 最初の固定cross-model shape axisは、midpointで繰り返さなかった

次の研究では、問いをさらに小さくした。同じ5色×2形状panelを使い、式だけで決めた
5つの深度からraw-glyph `resid_post`を取り出す。Primaryはmidpointだけである。
色ごとにcircle vectorからsquare vectorを引き、5つの差分が一つのshape axisを共有するなら、
正規化後の方向が平行になるはずだ。Square labelの全120置換をexact nullとし、2つの
model cellを一つのHolm familyにまとめた。

2 cellのtoken構造は、意図的に分けてある。Gemma 2 2B 4-bitでは、10 glyphがすべて
別々のatomic tokenだった。OLMo 3 7B BF16では、全glyphが3 tokenで、shared prefixも
あった。それぞれのtokenizer構造で実行可能なmatchを先に宣言できた一方、model family、
scale、precision、tokenization、nodeは同時に変わっている。

Midpointの平行性は、Gemmaが`0.114857969`だった。全120 pairingのうち7件が同値以上で、
raw `p = 0.058333333`、Holm `p = 0.116666667`である。OLMoは
`0.024628040`、raw・Holm `p = 0.275`だった。どちらも棄却せず、凍結済み結果は
`no_dual_model_recurrence`となった。

Gemmaの非primary深度には、より小さな記述的p値もあった。公開表からは消さないが、
結果を見た後でmidpointと差し替えることもできない。OLMoでは、共通の
circle-minus-square軸が強まらない一方、同色circle-square pairingは深度とともに強まった。
この違いは次の問いを作る材料にはなるが、color表現やshape表現に名前を付ける根拠には
ならない。

Activation arrayは2本とも小さく、全量を公開できた。OLMo bundleはmac1、furnace relay、
mac2でbyte単位に一致し、runとjoint analysisのvalidatorもすべて合格している。
[T2の全結果](MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.ja.md)は、完全性の保たれた
負・mixed observational resultである。Shape geometryが存在しないとも、7B modelで
消えたとも言わない。固定したmidpoint recurrence claimが、2-cellの判定規則を通らなかった。

## 5 familyの格子は、atomic tokenと共有suffixを分けた

T3では、公開済みの10 emoji × 5 familyをそのまま使い、正確な
5 × 10格子を作った。Family間でslot labelをそろえ、式だけで決めた
5つの深度からraw-glyph `resid_post`を取得した。主統計量は事前に固定して
ある。Family平均を引いた残りのactivation変動のうち、共通slotが説明する
比率を5深度で等重み平均した。19,999回の同期nullと2 modelのHolm familyで
判定している。

Tokenizationが、2つのcellをはっきり分けた。Gemmaでは50 glyphがすべて
別々のatomic tokenになる。All-depthのslot比率は`0.204304805`、null平均は
`0.199984463`、Holm `p = 0.208500`だった。OLMoでは全glyphが
`[shared_prefix, family_token, slot_token]`となり、5 familyが同じslotで
厳密に同じ末尾tokenを使う。Slot比率は`0.500391869`、null平均は
`0.200184835`、Holm `p = 0.000100`だった。登録済みの結果は
`olmo_only_token_structured_recurrence`である。

OLMoのslot比率は最初の固定深度で最も大きく、stackに沿って
`0.994722`から`0.295828`まで下がった。共通token由来のgeometryが、層を進むにつれて
混ざっていくという見方とは整合する。ただし、そのmechanismを検証したわけではない。
Model family、size、precision、nodeも同時に変わる。そのため
[T3の全結果](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.ja.md)では、token構造を
OLMoの観測に対する十分な代替説明として扱う。Tokenizerの因果性や絵文字の
意味の証明ではない。

## 1つ後ろの共通tokenにも、OLMoの配置は残った

T3には、安価に反証できる点が一つ残っていた。OLMoの結果は、現在位置で共有slot token
そのものを読んだから見えただけかもしれない。そこでT4では、読み出しを厳密に1 token
後ろへ移した。全絵文字に同じperiodまたはnewlineを加え、その位置の`resid_post`を
測った。生の絵文字token列は直前のprefixに残るが、各文脈内の現在tokenは50項目すべてで
同一になる。

2文脈×5深度のGemma統計は`0.203443011`、null平均`0.200044692`、Holm
`p = 0.302950`だった。OLMoは`0.537464703`、null平均`0.199977865`、Holm
`p = 0.000100`だった。登録済みの結果は`olmo_only_common_suffix_carryover`である。
OLMoの文脈別統計も、period `0.538985382`、newline `0.535944025`とほぼ同じだった。

これで説明は一段狭くなった。T3の配置は、slot tokenそのものを読む瞬間だけに閉じて
いない。次の共通tokenに対する最初のblock出力ですでに見え、stackを進むにつれて弱く
なる。ただし、絵文字の意味を見つけたわけではない。Transformerはprefixの情報を現在
位置へ混ぜる。OLMoの明示的な`[family_token, slot_token]`構造が短距離で伝わるだけで、
まだ十分に説明できる。

[T4の全結果](MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.ja.md)では、2本のarrayと
全20文脈×深度rowを公開した。次に問うなら意味ラベルではなく距離である。同じcarrier
tokenを何個はさんだところで配置が消えるのか。ただし新しいprotocolとして固定する必要が
あり、tokenization-matched確認controlの代わりにはならない。

## 8個の共通carrier tokenでも、登録した減衰は得られなかった

T5では、その距離の問いを新しいmodel forwardより先に固定した。すべての絵文字の後ろへ、
同じ`" a"` tokenまたは同じ`" |"` tokenを8個置いた。入力全体は変えず、読み出し位置だけを
距離1、2、4、8へ動かした。Gemma 2 2B、Llama 3.2 3B、OLMo 3 7Bについて、5つの
固定深度を測った。

正の判定は意図的に厳しくした。各modelは、距離1のmatched-slot再現と、log距離に対する
正の固定減衰contrastの両方を示す必要がある。2つのp値の大きい方をmodelのraw p値とし、
3 modelをまとめてHolm補正した。

通過したmodelはなかった。Gemmaは距離1の再現を示さなかった。LlamaとOLMoはこの成分を
permutation下限で棄却したが、減衰p値はLlamaが`0.188`、OLMoが`0.9977`だった。
登録済みoutcomeは`no_model_distance_attenuation`である。

この負の判定は、結果を見た後の正の物語より重要である。Llamaの距離profileは
`0.379, 0.414, 0.396, 0.369`、OLMoは`0.480, 0.519, 0.513, 0.527`だった。
どちらも単純なmodel-level減衰曲線には従わず、距離8でも記述的には高い。ただしtailは
副次値であり、主減衰仮説が失敗したからといって、新しい発見へ差し替えることはできない。

完全なprofileは、次のprotocolに使える手がかりを一つ残した。LlamaとOLMoでは、最初の
捕捉layerは距離とともに下がる一方、後半の深度は平坦または上昇する。後半blockがslot変数を
再構成した証明ではない。Interactionは主検定ではなかったからだ。結果を見た後で初期layerだけを
選ぶと誤解を招くことは分かる。次はinteraction自体を固定するか、同じartifact上で共有slot構造を
壊す必要がある。

[T5の全結果](MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.ja.md)には、3本のarray、120個すべての
carrier×距離×深度row、失敗した主判定、3 nodeの転送証拠を公開した。これはtokenizer条件付きの
geometryに関する観測証拠であり、絵文字の意味や因果的memoryではない。

## 4つのdense CUDA cellでも、負のconjunctionが繰り返された

T6はT5のendpoint全体を保ち、model rosterと実行cellを変えた。T6 forwardより前に、炉へ
完備されたGemma 2 2B IT、Gemma 3 4B IT、Mistral 7B Instruct v0.3、Gemma 3 12B ITの
4つのBF16 Transformers/CUDA roleを固定した。RosterはT5の後に選んだため、prospective
なのは未観測だったT6自身のoutcomeに対してだけである。

今回も通過modelはなかった。Gemma 2 2BとGemma 3の2 cellは、距離1でmatched null付近に
残った。Mistralは異なり、距離1統計はnull平均約`0.2`に対して`0.3845`、permutation下限
`0.00005`だった。しかし減衰p値は`0.46975`で、conjunctionは失敗した。4つのHolm補正済み
IUT p値はすべて`1.0`で、登録済みoutcomeは`no_dense_model_distance_attenuation`である。

この分岐は「大きいmodelほど効く」という標語より有益である。Mistralは距離8でも
`0.3930`と記述的に高く、Gemma 3 12Bには名目的な副次tail p値`0.04045`があった。
どちらにも多重性判定の権限はない。Gemma 3の4Bと12Bは観測tokenizer rosterを共有するが、
選択した1 pairだけではscale lawを同定できない。4 cellはmodel familyとtokenizerが異なり、
すべてinstruction-tunedなので、T6は独立確認でもbackend parity実験でもない。

運用境界も守った。炉が空いていることを再確認し、現在の`resource:furnace`通知が自然な
receiver-owned Codex lifecycle境界でsurfaceしてから計算した。通知本文は自動取得せず、返信、
commitment、6 sessionへのdeliveryも主張しない。1,600 forward、4 array、160 profile row、
validator、返送ledgerは[T6の全結果](MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.ja.md)に
まとめた。

このphaseのendpointについては、model幅を十分に試した。次は同じartifact上で共有slot構造を
壊すcontrolか、距離×深度interaction自体を事前固定する方が綺麗である。構造をほどかずに
modelを追加しても、主に交絡を増やすことになる。

## Base checkpointでは、深度interactionが見えた

T7では、その2つ目の選択肢を採った。T6の後、T7 forwardを1回も行う前に、Mistral 7B
v0.3 baseの1 cellと、2条件を同時に要求するendpointを固定した。条件は、距離1で反復することと、
最初に捕捉した深度の減衰が後期4深度の平均より強いことである。50 glyph、2 carrier、4 distance、
5つの相対深度はそのまま保ち、介入や生成は加えていない。

今回はconjunctionが通った。距離1の反復は`0.377524026`で、同期slot permutationのnull平均は
`0.199970302`だった。固定した初期−後期interactionは`0.149104068`、null平均は
`0.000111606`である。19,999 drawによる片側p値はいずれも`0.00005`の下限に達した。最初の
深度では正の減衰（`+0.114009450`）があり、後期4深度の平均はわずかに負
（`-0.035094618`）だった。5深度を平均するとこの分岐は隠れる。以前の全深度減衰統計は
`-0.005273805`、`p = 0.87475`だった。

形は、すでに観測済みだったInstruct profileと驚くほど近い。20個の深度×距離cellについて、
記述的な相関は`0.996785730`、MAEは`0.011953404`である。ただし、この見た目の一致は手がかりで
あって効果推定ではない。Endpointとbase checkpointはT6を見た後に選び、2 checkpointは関連して
いる。したがってT7からinstruction tuningが何を変えたかは分からず、独立確認にもならず、この
観測geometryを意味や因果のclaimへ変えることもできない。

狭い固定scopeの中で分かったのは、Mistralの反復が深度方向に単純な平坦形ではないことである。
初期layerで最も強く、その後は持続する後期profileへ落ち着く。次の綺麗な実験では、共有slot構造を
壊しながらこのinteractionを直接狙うか、新しいfreezeの下で無関係なcheckpointへ移れる。
[T7の全結果](MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.ja.md)には、40個すべてのprofile row、
compact activation array、transfer receipt、正の一次結果と同時に負のclaim境界も残した。

## より大きなモデルは、技術ゲートを通過しなかった

E2では、新しい科学的な結果を見る前に、固定したLlama 3.2 3B BF16 cellへ同じ
MLX経路を採用できるか検証した。最初に凍結した試行は、MLXのBF16 arrayをNumPyへ
渡す箇所でerrorとなり、停止した。この失敗記録は残している。V2では、NumPy export
の時点だけBF16 arrayをFP32へcastするbridgeを追加し、model実行はnative BF16の
まま保った。今度は、2つのbackend phaseを最後まで実行できた。

ただし、完走は適格性を意味しない。V2レシートの判定は
`status: validation_failed`、`scientific_result: false`で、parity検査60件中
33件が合格した。Tokenization、
backend内の決定性、厳密なzero-hookは合格した。Activation差分も10件すべてが
閾値内だった。一方、対応するlogit差分は大きく外れ、複合差分は0 / 10、固定した
介入忠実度も0 / 10だった。介入忠実度のactivation NRMSEは、閾値0.01に対して
約0.0302〜0.0341である。Cosineは約0.9994、RMS ratioは約1だった。

この記録では、MLXは速度でも遅かった。Aggregate median latencyは、
Transformers/MPSが132.127833 ms、MLXが230.138000 msで、記録上のspeedupは
`0.574124367x`である。速度gateは不合格となった。この値は、特定のマシン、
実行順、software、model、計測境界に依存する。MLX全般の評価ではない。

重要なのは、gateが意図どおりに働いたことである。研究用target bankや科学的outcomeを
開く前に、不適格な技術経路を止めた。Llamaで絵文字familyのgridは実行していない。
したがって、絵文字についての負の結果でも、modelをまたぐ再現でもない。
[E2の全結果](LLAMA32_3B_MLX_VALIDATION_RESULTS.ja.md)には、activationの一致、
logitの不一致、速度gateの失敗、科学的な主張境界をまとめている。

続いて、runtime compute dtypeだけを変えれば、同じBF16-weight artifactから適格な
経路を作れるかをStage A3で調べた。これも実行前に条件を凍結した。FP16とFP32は、
identity、決定性、zero vector、backend内の介入忠実度に合格した。止まったのは
速度である。FP16のMLXは、Transformers/MPSの1.9567倍の時間を要した。FP32のMLXは
約1.4%速かったものの、規則が求めた5%以上の短縮には届かなかった。候補は選ばれて
いない。また、Stage A3ではbackend間のfull parity familyを実行していないため、
FP32の適格性も、50絵文字の科学gridも許可しない。
[Stage A3の全結果](LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.ja.md)では、この技術上の
no-goを、Llamaや絵文字に関する主張と明確に分けている。

## T8: 大規模atlasによって次の意味問題を検定可能にする

T8では、将来の確認集合を消費せず、空いたfurnace時間を広い取得に使った。Model forward 0の
censusで、fully-qualified単一codepoint emoji 1,184件を、既出calibration 50件、未使用
discovery 842件、決定的なreserve 292件へ分けた。取得gridは、glyph、Unicode正式名、
`U+...` literalの3表現と、2 carrier、4 readout距離、9深度を交差させた。

速く完走したことだけを理由に最速runは採用しなかった。Batch size 64はgridを短時間で
完了したが、固定したbatch-one recapture 18 caseすべてに失敗した。閾値と失敗記録を残し、
同じ892件を5,352回のbatch-one callで再取得した。28 shardはすべて検証に合格し、別の
18-case repeatはbit-exactだった。このためcanonicalなのはbatch-one atlasである。失敗した
batch-64 runのaggregate profileが近いことは、vector-level不一致を修復しない。

Discovery patternは、真の確認stepを設計する価値があるほど強い。Layer 31の平均
glyph→name top-1 retrievalは`0.136580`、chanceは`0.001188`、glyph→codepointは
`0.001188`だった。厳密に5 tokenで共通3-token prefixを持つ760 glyphへ限定しても、
glyph/name token数が等しい43件へ限定してもcontrastは残った。ただし、この層別は主結果を
見た後に指定している。確認ではなく、完全token-isomorphicでもない感度解析である。

そのprospective stepは完了した。Reserve forward前に、layer 31の8 carrier×distance cellにおける
glyph/name minus codepoint top-1 contrastの最小値を、単一global statisticとしてfreezeした。
その後292件を一度ずつ取得した。最小contrastは下限`0.02`に対して`0.171233`、共通permutation
19,999回のうち観測統計以上は0回だった（`p = 0.00005`）。Alignment候補は確認され、T8の
reserve questionは閉じた。

主張境界は広がるのではなく、より鋭くなった。Primary retrieval contrastは8 cellすべて通過したが、
secondary CKA contrastは1 cellでわずかに負だった。支持されるのは、このmodel・layerにおける
正しいitem-name対応の頑健性であり、すべてのgeometry measureの一様な優位、絵文字意味
そのもの、因果mechanism、model一般性ではない。[Discovery結果](MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1_RESULTS.ja.md)と
[reserve確認](MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0_RESULTS.ja.md)に、両段階とevidence hashを残した。

## T10: 統計的なalignmentは、実用条件を満たすモデル横断再現にはならなかった

T10では、T9のpopulation、view、carrier、距離、batch rule、返却された最終state endpointを固定したまま、
item-name retrieval差が複数のmodel/tokenizer cellで同じ統計条件と実用条件を満たすかを問うた。Model rosterと
判定規則は、候補modelへforwardする前に固定した。

結果は明確に二つへ分かれた。9つのmodel-cell IUTはすべて統計的に有意で、4つのcore cellによる
部分連言p値は`0.0001`だった。3 viewのtoken数を完全一致させた層にも281〜287項目が残り、最小差は
全項目成分に近いままだった。したがって、token数の層が揃っていないことだけでは、pattern全体を説明できない。

ただし、仮説は有意性だけではなかった。実用条件は、4つのcore cell中3つ以上で、両成分の最小差が
`0.02`以上になることを求めた。通過したのはLlama 3.2 3B baseとQwen 2.5 7B baseだけである。
OLMoは全項目成分、Gemmaは両成分で下限を下回った。したがって登録済みoutcomeは、
`cross_model_replication_not_established_under_frozen_rule`となる。

観測後に閾値を修理するより、この負の一次判定を残す方が情報量は多い。固定assayではalignmentの向きが
広く見える一方、完全gridでの大きさは、固定したcore rosterをまたいでまだ頑健ではない。単調なQwen size
profile、強い関連Mistral-Instruct cell、raw-block endpointとの差は、scale、tuning、mechanismの結論ではなく、
次の記述的手掛かりにとどめる。[T10結果](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.ja.md)には、
統計条件と実用条件の分岐、および9セルすべてを残した。

## ここから言えること、まだ言えないこと

固定したGPT-2 FP32 MLX `resid_post`セルでは、layer 2が、3つの指定済みトークン数・接頭構造matched panelに対して、2種類のsource-wrapper構成で正の超過を保った。凍結済みv1規則では、両方とも頑健と判定された。Layer 4は通過していない。

ただし、トークン化から独立したglyph効果とは呼べない。GPT-2に茶色い丸の概念があるとも、特定のattention headやMLPがglyph featureを担うとも、人が読める意味を方向が運んでいるとも、別モデルへ一般化するとも言えない。独立ソース条件は同じターゲットを使っており、独立モデルや独立ターゲットでの再現ではない。完了した二次診断は、2つのトークン構造問題を記述的に絞り込むが、同等性を示さず、主張からトークン化を取り除くものでもない。

`causal_claim_authorized`は、いまも`false`である。C1 v1は実験model、tokenizer、outcome解析には使っていない。ただし、read-only検索の範囲が広すぎたため、1レコードが研究agentの文脈へ表示された。そのためbank全体を廃止した。詳細は[holdout状態](HOLDOUT_STATUS.ja.md)に示す。
E1もこの境界を変えず、意味、tokenizer非依存性、layer固有性、random controlに
対する頑健性を確立しない。
T2から加わるのは、範囲を限ったcross-model non-recurrenceである。事前指定したmidpointは
どちらもHolm補正後に棄却しなかった。ただし、不均一性の原因も、colored-shape geometryの
不在も示さない。
T3からは、tokenizer条件に沿う分岐が加わる。厳密に同じ末尾slot tokenを
共有するOLMo cellは固定omnibus nullを棄却し、Gemmaのatomic-token cellは
棄却しなかった。ただし、model cell間で複数の条件が同時に変わるため、token構造に
よる代替説明は支持しても、token identityを原因とは同定できない。
T4からは、もう一つ境界が加わる。OLMoの分岐は、固定した2文脈で1つ後ろの共通tokenにも
残った。現在tokenだけの説明は退くが、構造化prefixからの短距離伝播は退かない。
T5からは、持続距離に関する負の結果が加わる。Gemma、Llama、OLMoのいずれも、距離1の
再現と正のmodel-level減衰を同時に要求した登録済み検定を通過しなかった。LlamaとOLMoは
距離8でも記述的には高いが、tailとdepth interactionは副次結果であり、持続、意味、機構の
主張を認めない。
T6でも、選択した4つのdense CUDA cellで同じ負のconjunctionが繰り返された。Mistralは強い
recurrence成分を保ったが、固定した減衰成分を通らず、3つのGemma cellは距離1を棄却しない。
Model scale、tokenizer同等性、backend parity、確認は示さない。
T7では、それまで未観測だったMistral base checkpointの深度interactionをprospectiveに検定し、
固定した両成分を棄却した。ただしendpointと関連checkpointはT6後に選んでいる。Instruction
tuning効果でも独立確認でもなく、Phase I gateも閉じない。
T10からは、claim-matchedな9セル結果が加わる。Token数完全一致後も観測差は消えなかったが、固定した
実用下限を満たしたcore cellは4つ中2つだった。支持されるのは3つの範囲限定model/tokenizer-cell
alignmentと負のモデル横断一次判定であり、tokenization非依存性、scale、tuning、意味、因果、独立再現、
model一般性ではない。

## 次は、因果プロトコルを凍結する

運用上のMilestone 2は完了した。Layer 2は、新しい対象限定型の因果プロトコルを設計できる段階に入った。Layer 4は未解決のままで、候補にはしない。ここで認めるのはプロトコル設計であり、因果主張ではない。廃止済みC1 v1はこの実験に使えない。露出した研究文脈の外で新しいversionの因果bankを用意し、公開freezeまで未使用に保つ必要がある。E1はこのlayer候補を選び直す根拠にはしない。E1から仮説を絞る場合も、別の公開プロトコルと新しい未使用target bankが必要になる。

T2は完了しており、primary layerを動かして救済しない。5 familyへ広げる
選択肢は、T2の判定に後付けせず、別protocolのT3として固定・完了した。T4もT3のsubcellを
救済せず、1 token carryoverを事前に固定して検証した。T5は単純なmodel-level carrier距離
減衰を固定し、その説明を棄却した。T6も選択した4つのdense CUDA cellで同じconjunctionを
保ち、やはり通過modelはなかった。続くT7では深度×距離interaction自体を固定し、未観測だった
Mistral base cellの1 model IUTを棄却した。隣接modelをさらに増やす優先度は下がった。残る
綺麗な選択肢は、同じartifact上で共有slot構造だけを壊すcontrolか、固定interactionの真に独立した
追試である。どちらも新しいprotocolを要する。

T10も完了しており、実用下限を下げたり、core modelを入れ替えたり、extension cellを昇格させたりして
救済しない。次の分岐は明示できる。Mixed resultとして論文へ残す、最終claimに合う真に独立した追試を設計する、
またはT11を変則glyphの探索として明確にラベル付けして開く、のいずれかである。T11は未着手のままで、T10を
遡って変更できない。

E2では、研究責任者がTransformers/MPS専用の科学経路を別に選択した。V1は、auditがraw tokenizationとwrapper内のcontextual tokenizationを混同したため、model weightの読み込みもforwardも行う前にtokenizer preflightで停止し、科学的outcomeを持たない。元の50絵文字armと、別々にcenteringする35絵文字token-structure感度armは、修正済みの[E2 MPS transport v2プロトコル](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.ja.md)へoutcomeを見る前に改めて固定する。MLXのno-goをpassに変えず、MLX v2とStage A3の閾値も変更しない。

将来の新しいversionの因果bankは、候補、介入部位と操作、endpoint、対照、多重性familyをsealed patch–ablate–restoreプロトコルに固定するまで開かない。独立backendと、別modelまたはtokenizerでの再現も残っている。論文での最終的な確認表現と、それを支える再現実験では、科学的roleを凍結済みinputへ事前に直接結び付け、データ依存prototypeの再標本化を扱う。

Phase Iの終点は、結果が正でも、混合でも、負でも、英語論文だ。論文ではlayer 2と4を一緒に示し、凍結済みv1推論と事後感度分析を区別し、完了した診断、T2 non-recurrence、T3のtokenizer条件に沿う分岐、T4の1 token carryoverを、それぞれの主張境界とともに示す。そして、ひとつひとつの文を凍結済みartifactへ戻せるようにする。
T5で失敗した減衰endpointと、持続して見える完全な記述profileも同じ記録へ含める。都合のよい
距離、carrier、深度へ差し替えてはならない。
T6の4つのnon-rejection、Mistralの成分分岐、160 rowすべても記録へ含め、tail、深度、model
pairを格上げしてはならない。
T7の正の深度interactionと40 rowすべても、そのT6後のmodel選択と非確認的statusを明記して
並べる。
T8/T9の正の単一model reserve確認と、T10の負のモデル横断一次判定も並べて示す。Token数matching後も
signalは残ったが、実用下限を通過したcore cellは2つだけで、tokenizer非依存性やmodel一般性は認めなかったと
明記する。

最初の地図は、前より鮮明になった。同時に、読みすぎにくくもなった。対照を入れた意味は、まさにそこにある。
