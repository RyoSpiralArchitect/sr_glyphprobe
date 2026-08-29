# Emoji Steering Specificity Atlas v0 — T13の設計図

[English](EMOJI_STEERING_SPECIFICITY_ATLAS_V0.md) · [T12結果](GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.ja.md) · [ロードマップ](ROADMAP.ja.md) · [Phase I論文構成](PAPER_OUTLINE.ja.md)

状態: **future workの選択肢を整理した文書。事前登録ではなく、確認実験の実行許可も
与えない**。

T13のmodel forward、保護対象bankへのtokenizer処理、intervention、generation、
target選択、endpoint選択、threshold選択は、まだ一度も行っていない。この文書では、
結果に応じた複数の綺麗な着地点を意図的に残している。炉の空き状況によってscheduleや
shardの大きさを変えてもよいが、科学的endpointや判定規則を変えてはならない。

## なぜ今、最初の問いへ戻るのか

この研究は、「絵文字由来directionでsteerすると、何か特異なことが起きるのか」という
広い問いから始まった。その後の証拠によって、いくつかの簡単な説明を順番に取り除いてきた。

- 共有token構造だけでも強いmatched-slot recurrenceが生じ、共通suffixまで持ち越される。
- 単純なdistance attenuationは、凍結したAND条件では再現しなかった。
- Glyph/name alignmentは単一modelで大きく、より広いrosterで正方向に揃っても、
  実用的なmodel横断ruleを満たさないことがある。
- T11ではZWJとregionalにsystem固有の候補が見えたが、T12では未使用reserveにおいて
  どちらも確認されなかった。

したがってT12の負の結果は、通るまでglyph panelを広げる理由ではない。最初の問いを、
より厳密に立て直す理由である。「絵文字特異的」と呼ぶには、lexical、token構造、rarity、
位置、random directionという代替説明を明示的に検定した後にも、介入効果が残らなければ
ならない。

## 後で凍結する問い

> Source prompt、介入位置と強度、carrier位置、target prompt、random controlを固定した
> とき、絵文字由来directionは、意味を揃えたword、decomposed Unicode、token構造を
> 揃えた非絵文字、normを揃えたnull directionよりも選択的にmodel behaviorを変えるか。

これはintervention specificityの問いであり、「glyphとnameのactivationが近いか」という
観測的geometryの問いとは別である。両方のlaneに価値はあるが、観測geometryをsteeringと
呼んではならない。

## Source family

T13で選ぶ各semantic conceptについて、modelごとにpreflightしたsource familyを作る。

1. **Emoji glyph** — 候補となる表示済みUnicode sequence
2. **Official-name text** — 同じreferentを表す、正規化Unicode nameまたは固定label
3. **Decomposed form** — presentation、joiner、regional fusionを外してscalar componentを
   分離した形式
4. **Matched non-emoji Unicode** — token数、prefix/suffix pattern、位置、corpus rarityを
   可能な限り揃えたsymbolまたはsequence
5. **Matched ordinary text** — token数、lexical frequency、source-wrapper構造を揃えた
   非絵文字phrase
6. **Null direction** — target outcomeを使わず作るzero、norm-matched random、
   orthogonalized random direction

Controlはtokenizer output classごとに別々に凍結する。Qwenで構造が一致したcontrolを、
tokenizationの異なるLlama、Gemma、OLMo、SmolLM、Mistralへ暗黙に流用しない。

## 何を「特異」と数えるか

新しい確認設計でemoji-specific candidateと呼ぶには、次をすべて満たす必要がある。

- 未使用target bankで、emoji-minus-best-matched-controlのprimary効果が正
- 小さいp値だけでなく、事前指定した実用床を通過
- 介入directionの符号を反転すると効果も反転
- outcomeを見てclippingを選ばず、固定した強度で順序あるdose response
- 全体的なlogitやentropyの移動ではなく、意図したtarget familyに対するselectivity
- exact token-countと、申告済みprefix/suffix感度を通過
- 事前指定した数のmodel roleで成功し、反対方向のroleも隠さず保持
- 登録したsource-family × endpoint仮説family全体で多重性を補正

これらを通過しても主張できるのは、固定rosterにおいて、申告したcontrolでは再現しない
intervention behaviorがemoji-derived directionにあった、という限定的な運用上の結論である。
人間のような絵文字理解、固有回路、tokenizer非依存性、tested populationを越える一般性は
まだ確立しない。

## 分離した2つのlane

### Lane A — representation audit

Lane Aは比較的安価な観測研究である。Glyph、name、decomposition、matched controlが、
depth、carrier、modelをまたいでどこで整列するかを調べる。Interventionもgenerationも
行わない。目的はbehavioral gridへ進む前に弱いsource constructionを落とすことであって、
steering claimを作ることではない。

最初の綺麗なatlasは、matched controlと固定normalized depthを持つ、source class ×
target classのselectivity matrixである。ZWJとregional flagは複数code pointから
表示形を作るためstress testとして有用だが、T12 outcomeから新しいendpointやthresholdを
選んではならない。

### Lane B — intervention specificity

Lane Bは因果的behavior testである。Scalar量を揃えたdirectionを、固定site、符号、強度、
prompt、target scoring ruleで比較する。必須armはemoji、official-name text、decomposed form、
最も強いeligibleな非絵文字/token control、random、sign-flip、zero interventionである。

Generationはblindなsecondary readoutにはできるが、primary endpointはsealed target bank上の
決定論的paired scoreとする。自由生成例は登録済み定量結果の例示には使えても、結果選択には
使わない。

## Confirmationを汚さない段階設計

### T13-E — exploratory source / endpoint screen

- 再利用可能と公開指定済みのexploratory target、または新しい探索用setだけを使う。
- Modelをloadする前に、9 tokenizer roleすべてをpreflightする。
- 9 modelのrepresentation atlas全体をresume可能なshardで取得する。
- Outcomeを見る前に選んだ代表3 role、すなわちsmall base、3B級base、7B級model各1本で、
  限定intervention pilotを行う。
- すべてのsource family、符号、強度、site、modelを報告し、confirmatory statusは付けない。

### T13-C — one-shot specificity confirmation

- 現在の研究文脈の外側で、新しい未使用target bankを作る。
- Targetへのtokenizeやmodel forwardより前に、primary endpoint、実用床、model roster、
  site/strength rule、control eligibility、停止rule、多重性familyを凍結する。
- P2と廃止済みC1 v1は再利用しない。
- Designとcompute budgetを受け入れた場合は、凍結した9 roleすべてを1回のacquisitionとして
  実行する。炉の空きに応じてshard境界を変えても、estimandは完全rosterのままにする。
- Outcomeは一度だけ開き、失敗cellと不均一cellをすべて保存し、別siteや別endpointによる
  救済を禁じる。

T13-Eを使ってT13-Cを設計してよいが、T13-Eの観測値をT13-Cのtest statisticへ混ぜない。

## 競合説明と綺麗な着地点

| Outcome | 現時点で最も妥当な解釈 | 論文 / future workでの着地 |
|---|---|---|
| Emojiがdose/sign control付きで全matched sourceとnullを上回る | 限定的なemoji-source intervention specificity | 最も強いT13-C候補。Mechanismはfuture work |
| Emojiとofficial-name textが同等で、両者がstructural controlを上回る | 共有lexical/referential route | 「特異ではない」という有益な結果。Source efficiencyを比較 |
| Emojiとmatched non-emoji Unicodeが同様に動く | token構造、rarity、orthographyで十分 | tokenizer-conditioned account。Emoji特異性は主張しない |
| ZWJ / regional interactionだけが残る | Unicode composition conventionへの感度 | 一般的な絵文字意味ではなくjoiner/regional構成を研究 |
| Modelごとに局所的、または符号が不一致 | model-conditioned geometry | 異質性を公開し、平均して一般性を作らない |
| どのarmも実用床を越えない | tested steering designに対する限定null | 負の結果としてPhase Iを綺麗に閉じる |

対応するoutcomeを開く前に選んでおけば、6つの着地はいずれも公開可能である。

## Computeを考慮したqueue

効率のよい順序は次の通り。

1. 保護targetへ触れず、tokenizerとartifact preflightを完了する。
2. Modelごとのcontrol eligibilityとshard manifestを凍結する。
3. 炉が空いている間に9 modelの観測atlasを取得する。
4. 代表3 roleのexploratory intervention pilotを、小さくresume可能なblockで回す。
5. Confirmation bankを作成・開封する前に、T13-Cをworkshop paperへ入れる価値があるか、
   future workに完全に回すかを判断する。
6. 実行が許可された場合は、競合でscheduleが中断しても登録estimandを変えず、
   T13-Cの9 roleをすべて完走する。

これなら勢いを保ちつつ、resource availabilityが隠れたmodel選択や停止ruleになることを
防げる。

## Workshopとの境界

現在のPhase I paperは、T13-Cの完了を必要としない。T10の凍結済みnegative replication
rule、T11 discovery atlas、T12 one-shot negative confirmationを組み合わせると、
token-matched control、実用床、model heterogeneity、未使用reserveがなぜ必要かを示す
一貫した物語になる。T13は、次の反証可能な実験としてfuture workへ置ける。

提出前にT13探索結果を追加する場合は、post-T12 exploratoryと明記し、保護bankを使わず、
T12解釈を変更しない。Paper freezeまでに独立検証できない結果はfuture workに残す。
