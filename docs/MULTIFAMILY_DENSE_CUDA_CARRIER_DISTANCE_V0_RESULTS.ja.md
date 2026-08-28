# Multifamily dense CUDA carrier-distance v0 結果

[English](MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.md) · [固定プロトコル](MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0.ja.md) · [T5結果](MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.ja.md) · [公開証拠](../artifacts/multifamily_dense_cuda_carrier_distance_v0/README.ja.md) · [研究ロードマップ](ROADMAP.ja.md)

## 状態

固定した4つのBF16 Transformers/CUDA roleとjoint analysisはすべて完了した。事前登録した
outcome patternは次のとおりである。

```text
no_dense_model_distance_attenuation
```

4つのmodel-level intersection-union testは、いずれもHolm補正後に棄却されなかった。
Gemma 2 2B IT、Gemma 3 4B IT、Gemma 3 12B ITは距離1成分を棄却しなかった。
Mistral 7B Instruct v0.3はその成分を強く棄却したが、固定した正のlog距離減衰成分を
棄却しなかった。

これは、T6で固定したrecurrence-plus-attenuation conjunctionに対する明確な負の結果で
ある。すべてのlayerやcarrierで減衰がないことを示す結果ではない。

## 唯一の主判定

各modelについて、基準Aは距離1のmatched-slot比率を等重み平均した値である。基準Bは
距離`[1, 2, 4, 8]`へ重み`[0.375, 0.125, -0.125, -0.375]`を与えた固定contrastで
ある。Modelのraw p値には`max(p_A, p_B)`を用いるため、両成分の棄却が必要になる。
4 modelのraw p値を1つのHolm familyとした。

| Model | 距離1統計 | 距離1 null | A raw p | 減衰統計 | 減衰null | B raw p | IUT raw p | Holm p | 棄却 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Gemma 2 2B IT | 0.193651440 | 0.200026712 | 0.765300 | -0.002917767 | -0.000010763 | 0.770900 | 0.770900 | 1.000000 | しない |
| Gemma 3 4B IT | 0.188406654 | 0.199900049 | 0.753000 | -0.011727577 | +0.000054641 | 0.845150 | 0.845150 | 1.000000 | しない |
| Mistral 7B Instruct v0.3 | 0.384482548 | 0.199919677 | 0.000050 | +0.000672124 | -0.000043576 | 0.469750 | 0.469750 | 1.000000 | しない |
| Gemma 3 12B IT | 0.183050961 | 0.199966981 | 0.825800 | -0.021082592 | -0.000052892 | 0.975750 | 0.975750 | 1.000000 | しない |

`0.000050`は、19,999回のpermutationと観測配置から得られる最小値であり、それ以上の
精度を意味しない。Mistralの減衰contrastはわずかに正だったが有意ではない。Gemma 3の
2 cellは、どちらも事前登録した減衰方向と逆符号だった。

## 固定距離profile

次の値は2 carrierと5深度を平均している。すべて副次記述であり、intersection-unionの
判定と差し替えることはできない。

| Model | 距離1 | 距離2 | 距離4 | 距離8 | 距離8の副次raw p |
|---|---:|---:|---:|---:|---:|
| Gemma 2 2B IT | 0.193651440 | 0.195496670 | 0.201573016 | 0.199406704 | 0.507350 |
| Gemma 3 4B IT | 0.188406654 | 0.205419840 | 0.210326645 | 0.218044590 | 0.188000 |
| Mistral 7B Instruct v0.3 | 0.384482548 | 0.424695499 | 0.393637011 | 0.393043048 | 0.000050 |
| Gemma 3 12B IT | 0.183050961 | 0.182362620 | 0.192866008 | 0.235770077 | 0.040450 |

Mistralは距離8でも約`0.2`のmatched nullを記述的には大きく上回る。Gemma 3 12Bにも
0.05未満の名目的な距離8副次p値がある。どちらのtail値にも独立した多重性判定はなく、
発見へ格上げしない。T6は、単調な持続、持続時間の閾値、因果的memory機構を示さない。

## Carrier別profile

Carrier別の値は副次結果である。各rowの4つの読み出しでは、8 tokenを含む入力全体を
同一に保っている。

| Model | Carrier | 距離1 | 距離2 | 距離4 | 距離8 |
|---|---|---:|---:|---:|---:|
| Gemma 2 2B IT | `" a"`の反復 | 0.193942238 | 0.195153619 | 0.202303842 | 0.196795220 |
| Gemma 2 2B IT | `" |"`の反復 | 0.193360641 | 0.195839721 | 0.200842190 | 0.202018188 |
| Gemma 3 4B IT | `" a"`の反復 | 0.180378195 | 0.216307034 | 0.156518699 | 0.184858562 |
| Gemma 3 4B IT | `" |"`の反復 | 0.196435112 | 0.194532646 | 0.264134591 | 0.251230617 |
| Mistral 7B Instruct v0.3 | `" a"`の反復 | 0.385470450 | 0.422491524 | 0.377625207 | 0.357273678 |
| Mistral 7B Instruct v0.3 | `" |"`の反復 | 0.383494646 | 0.426899475 | 0.409648814 | 0.428812418 |
| Gemma 3 12B IT | `" a"`の反復 | 0.189024470 | 0.178709143 | 0.199290295 | 0.260436081 |
| Gemma 3 12B IT | `" |"`の反復 | 0.177077452 | 0.186016098 | 0.186441720 | 0.211104072 |

Carrier依存の不均一性は見えるが、主contrastではない。結果を見た後に一方を選んでも、
失敗したconjunctionを修復できない。

## 距離×固定深度

各cellは2 carrierを平均している。80個すべてが副次値である。公開JSONLには同期nullの
summaryを含む160個のcarrier×距離×深度rowを完全に収録した。

### Gemma 2 2B IT

| 相対深度 | Layer | 距離1 | 距離2 | 距離4 | 距離8 |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 0 | 0.178408896 | 0.177829872 | 0.182219945 | 0.178008921 |
| 0.25 | 6 | 0.196489263 | 0.205349978 | 0.204058820 | 0.199496270 |
| 0.50 | 13 | 0.199276470 | 0.204185129 | 0.210253852 | 0.208743632 |
| 0.75 | 19 | 0.200012065 | 0.201508110 | 0.207531567 | 0.206843388 |
| 1.00 | 25 | 0.194070505 | 0.188610260 | 0.203800895 | 0.203941309 |

### Gemma 3 4B IT

| 相対深度 | Layer | 距離1 | 距離2 | 距離4 | 距離8 |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 0 | 0.208975752 | 0.221441832 | 0.191555699 | 0.199838396 |
| 0.25 | 8 | 0.185275609 | 0.258003841 | 0.324944730 | 0.337349991 |
| 0.50 | 17 | 0.181698088 | 0.190836943 | 0.195496968 | 0.166173881 |
| 0.75 | 25 | 0.189398911 | 0.186508348 | 0.185494081 | 0.178661841 |
| 1.00 | 33 | 0.176684910 | 0.170308238 | 0.154141746 | 0.208198840 |

### Mistral 7B Instruct v0.3

| 相対深度 | Layer | 距離1 | 距離2 | 距離4 | 距離8 |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 0 | 0.836365849 | 0.723139096 | 0.602677623 | 0.571511962 |
| 0.25 | 8 | 0.354806832 | 0.467365680 | 0.458334036 | 0.448617661 |
| 0.50 | 16 | 0.274185730 | 0.353431252 | 0.345568404 | 0.373585819 |
| 0.75 | 24 | 0.233429276 | 0.307482822 | 0.297952151 | 0.308080214 |
| 1.00 | 31 | 0.223625055 | 0.272058647 | 0.263652839 | 0.263419584 |

### Gemma 3 12B IT

| 相対深度 | Layer | 距離1 | 距離2 | 距離4 | 距離8 |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 0 | 0.222637362 | 0.201772776 | 0.187882197 | 0.174324369 |
| 0.25 | 12 | 0.184419588 | 0.200908226 | 0.194565696 | 0.206043671 |
| 0.50 | 24 | 0.174331769 | 0.186055128 | 0.174721814 | 0.255386295 |
| 0.75 | 36 | 0.179400665 | 0.189049205 | 0.206966252 | 0.337316831 |
| 1.00 | 47 | 0.154465420 | 0.134027768 | 0.200194079 | 0.205779217 |

Mistralの最初の捕捉layerは距離とともに下がるが、後半の固定深度は平坦または上昇する。
Gemma 3の4Bと12Bも、観測tokenizer rosterは同じだが、異なる非単調な深度profileを示す。
これらは結果確認後の記述である。特定componentによる再構成もmodel-scale効果も示さず、
検定するには新しいprospective interactionまたはmatched-pair protocolが必要になる。

## T5との関係

T5でも、同じ固定model-level conjunctionを通過したmodelはなかった。MistralのT6 profileは、
T5のmulti-token Llama・OLMo cellで高かった距離profileと記述的には似ている。一方、T6の
Gemma 3 cellはaggregateではmatched nullに近い。RosterはT5の後に選び、T6の4 modelは
すべてinstruction-tunedで、T5のMLX cellとは異なるTransformers/CUDA実行である。両研究を
推論へ統合せず、T6を独立確認やbackend parity testとは扱わない。

Gemma 3の4Bと12Bは観測tokenizer rosterが同じだが、選択したparameter数2点の1組はscale
標本ではない。両方のnon-rejectionからscale trendや同等性を主張しない。

## 整合性、実行、lifecycle gate

- 公開凍結commitは`5e2f4984486b5e5dc87b93f656d6e00bc8718baa`、manifest SHA-256は
  `997389551df07922e8dcacfffa93a97a2ffb97a9da23e2e86fbc64c73a829f06`である。
- 4 arrayのshapeは固定role順に`50 × 2 × 4 × 5 × 2304`、
  `50 × 2 × 4 × 5 × 2560`、`50 × 2 × 4 × 5 × 4096`、
  `50 × 2 × 4 × 5 × 3840`である。
- 各modelは400 forward、合計1,600 forwardを実行した。介入、生成、protected targetへの
  accessはいずれも0である。
- 4つのrun validator、返送した5つのSHA-256 ledger、160 rowのjoint analysis validatorは
  すべて合格した。各model後にGPUを解放し、最終run後もfreeへ戻った。
- 計算直前に炉が空いていることを確認し、現在の`resource:furnace`通知がmac2上の自然な
  receiver-owned Codex `Stop`境界でsurfaceした。Metadataだけを確認し、本文は取得して
  いない。返信、commitment、6 sessionへのtask-local deliveryも主張しない。
- 圧縮activation、observation、receipt、ledger、analysis、transfer receipt、public manifestを
  完全に公開する。

## 主張境界と次の判断

T6では、唯一のmodel-level intersection-union familyで棄却されたmodelはない。再現が
消失すること、すべてのlayerが同じ減衰則に従うこと、絵文字の意味が8 tokenにわたって
保存されることは示さない。機構、回路、architecture、scale、precision、tokenizer、node、
backend同等性、確認、Phase I paper gateについても結論しない。

このendpointに対するdense model幅の追加は、いったん十分である。次の綺麗な観測案は、
carrierと読み出し位置を保ちながら共有slot構造だけを壊すsame-artifact control、または
距離×深度interactionを別protocolで事前固定する追試である。T6を見た後にMistral、Gemma 3
12Bのtail、都合のよい深度を新しいprimaryに選んではならない。因果主張より前に、
tokenization-matched controlsと未使用confirmatory target setを固めるというPhase Iの
上位優先順位も変わらない。
