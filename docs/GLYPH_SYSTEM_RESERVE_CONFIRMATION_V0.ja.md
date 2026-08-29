# Glyph-System Reserve Confirmation v0（T12）

[English](GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0.md) · [T11結果](GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.ja.md) · [T11プロトコル](GLYPH_SYSTEM_DECOMPOSITION_V0.ja.md) · [ロードマップ](ROADMAP.ja.md)

状態: **前向きプロトコル。T12 reserveへのmodel forwardは0**。

T12では、T11で最も明瞭だった二つの変則glyph候補を、未使用reserve全件で一度だけ確認する。T11で示したZWJ単独案を意図的に広げ、次の2仮説を一つのfamilyとして扱う。

1. **H_ZWJ_FUSION:** ZWJ sequenceは、spaceで分解した形よりも、融合したglyphの方がofficial nameとのmatched-control調整済み関係が強い。
2. **H_REGIONAL_DUAL:** regional-indicator flagは、融合形ではofficial place nameを、ASCII分解形ではletter-component labelを同時に選好する。

Regional仮説は二度の成功機会ではなく、二つの条件をともに満たすintersection-union claimである。Component testは両方とも通過しなければならない。そのうえで、`H_ZWJ_FUSION`と`H_REGIONAL_DUAL`の2仮説にHolm補正を適用する。

## Regionalを含める理由

T11で最も拡散の小さかった単独候補は、ZWJの`presentation_or_fusion` contrastだった。72 cell中65 cellが正で、9 model中8 modelのcontext中央値が正、descriptive intervalが明確に負となったcellはなかった。一方、regional flagでは異なる、研究上重要な形が見えた。融合形はofficial place nameを選好し、ASCII分解形はcomponent-letter labelを選好した。Discovery中央値は、それぞれ`0.0668`と`0.0441`だった。

Regionalを加えることで、確認すべき問いは単に大きくなるのではなく、より鋭くなる。融合形の優位と、whole-sequence/componentの二重構造を区別できるためだ。ReserveはZWJ 96件、regional flag 64件に限られるので、計算量も収まる。

## 固定populationとacquisition

160件のidentityはT11 acquisition前に選び、公開済みである。T11ではmodel forwardを一度も受けておらず、このfreeze時点でもmodel outcomeは未観測のまま保たれている。

| System | Reserve全件 | Forwardするview |
|---|---:|---|
| ZWJ sequence | 96 | glyph、Unicode name、decomposed form |
| Regional-indicator flag | 64 | glyph、Unicode name、component name、decomposed form |

T12は、T11と同じ9 model/tokenizer cell、2種類の1-token carrier、4距離を再利用する。保存するendpointは`output.hidden_states[-1]`だけである。Raw last blockや中間depthは取得しないため、別endpointでprimary resultを救済する余地はない。

Item-view pairは544件。1 modelあたり1,088 unique forward、9 model全体で9,792 forwardとなる。各forwardから4距離をまとめて読み出す。保存対象はFP32 readout vector 39,168本で、interventionとgenerationは行わない。

## Matched control

Tokenizer、system、label viewごとに、target token数が完全に一致するstratum内から誤labelを選ぶ。二つ目のmappingでは、targetの先頭token IDも一致させる。いずれもhash順に並べた後の1-step cycleで決まり、self-matchは許さない。

Required controlのcoverageは`0.75`以上、first-token matched controlは`0.70`以上を必須とする。すべてのmappingはmodel weightをloadする前に固定する。Coverage gateを満たさないmodel cellは停止する。Outcomeを見てmappingを作り直したり、itemを差し替えたり、stratumやthresholdを緩めたりしない。

Query formを`q`、target labelを`t`、決定的に割り当てた誤labelを`w`とすると、item単位の調整済み関係は次式で定める。

`cos(q_i, t_i) - cos(q_i, t_w(i))`

Fusion contrastは、official nameに対するglyphの関係からdecomposed formの関係を引く。Component trackingでは、component labelに対するqueryの順序を逆にする。

## 登録検定

各elementary testには、72個のmodel × carrier-distance cellをすべて残す。Cell statisticは、eligible item contrastの中央値。Global statisticは、その72 cell中央値の中央値である。Null分布は、glyphとdecomposed query formをitem内で入れ替える49,999回のrandomizationで作る。同じUnicode itemには全model・全contextで共通のswapを使い、そのitemに伴うcontext間・model間依存を保つ。

| Elementary test | 実用下限 |
|---|---:|
| ZWJ presentation/fusion | `0.005` |
| Regional presentation/fusion | `0.02` |
| Regional component tracking | `0.02` |

実用下限はdiscovery結果を参考に決めたが、reserve forward前に固定する。いずれもT11 discovery中央値より低く、単に浮動小数点上で正というだけでは通らない値である。

Poolingだけでは成功としない。各elementary testには、次の条件もすべて課す。

- 9 model中6 model以上が実用下限を満たす。
- 負の実用下限以下となるmodelは最大1つ。
- First-token matched global statisticが正。
- First-token matched model summaryが9 model中6 model以上で正。

Model summaryは、8 contextのcell中央値をさらに中央値でまとめる。First-token sensitivityがrequired-control testの失敗を救済することはない。

`H_REGIONAL_DUAL`のhypothesis p-valueには、fusionとcomponent-trackingの大きい方を使い、二つのcomponent gateをともに必須とする。2仮説familyにはHolm法を適用し、familywise error rateを`0.05`に制御する。Holm decision、実用下限、model heterogeneity、strict-prefix sensitivityのすべてが一致した場合に限り、その仮説をconfirmedとする。

## 結果の分岐

どちらもconfirmedにならなくても、T12は二つのreserve questionを閉じる。想定する着地は次のとおり。

- 二つの候補がともに再現する。
- ZWJ fusionのみ再現し、Regionalの二重構造は再現しない。
- Regionalの二重構造のみ再現し、ZWJ fusionは再現しない。
- 凍結したruleでは、どちらも再現しない。
- Acquisitionまたは必須validity gateが失敗し、scientific decisionを出さない。

Regionalの片方だけが成功しても、conjunctionとしては失敗と記録する。登録gateを通らなかったmodel別・context別の正値は、descriptive resultにとどめる。

## 主張の境界

T12が正でも、支持できるのは、この固定9-cell rosterとtransport gridにおけるactivation-geometry上のoperational contrastがreserveで再現したことまでである。Emojiの意味理解、因果、機構、behavioral steering、tokenizer independence、scale law、instruction tuning effect、architecture generality、model population generality、独立再現は確立しない。T10を救済・変更する結果としても扱わない。

次の問いは、emoji由来のsteeringが、matched word、non-emoji Unicode symbol、punctuation、generic token directionと比べて特異かどうかである。これはT12 primary resultを封印した後、別の探索プロトコルで扱う。T12 reserve outcomeを使って本プロトコルを変更してはならない。

## Furnaceでの実行順

最初にcommit済みfreezeをauditする。次に、reserve model forwardを0に保ったまま、9 modelすべてのtokenizer・artifact preflightを実行する。Compute直前には必ずfurnaceの競合を確認し、別のGPU workloadが現れたら譲る。

```bash
python scripts/glyph_system_reserve_confirmation_v0.py audit-freeze

python scripts/glyph_system_reserve_confirmation_v0.py preflight-all \
  --output <preflight-dir>

python scripts/glyph_system_reserve_confirmation_v0.py run \
  --model-label <role> --preflight-directory <preflight-dir> \
  --output <runs-root>/<role>

python scripts/glyph_system_reserve_confirmation_v0.py finalize \
  --model-label <role> --preflight-directory <preflight-dir> \
  --run <runs-root>/<role>

python scripts/glyph_system_reserve_confirmation_v0.py analyze \
  --runs-root <runs-root> --preflight-directory <preflight-dir> \
  --output <analysis-dir>
```

完了済みshardは検証後にskipする。不完全なstageがあれば、自動再取得せず手動で判定する。Modelはfurnaceの固定済みlocal cacheからだけ解決し、runnerがdownloadすることはない。
