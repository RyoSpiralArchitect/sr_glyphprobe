# GlyphProbe v1 科学的コントラクト

[English](SCIENTIFIC_CONTRACT.md)

## 問い

GlyphProbe v1 が問うのは、glyph 由来の固定 activation direction が、介入量、clipping、source wrapper、
target case、random-direction control を明示した後でも、出力空間に再現可能な fingerprint を残すかどうかである。

モデル内で emoji が何を「意味する」から問いを始めない。数値的・幾何学的な前提が blind screening を生き残り、
さらに後続の限定的介入実験を通過するまで、意味論的・機構的解釈を保留する。

## 分析単位

主な sampling cluster は target prompt である。source-direction seed は、固定された wrapper subset から生成する
反復推定であり、独立した target 観測を増やさない。surface-server 経路の generation seed は sampling replicate で、
target 内にネストしたままとする。

## 標準的な estimand

内部経路は、glyph、layer、strength、source-direction seed の各組み合わせについて次を記録する。

1. 実現した摂動 RMS / target RMS 比と clipping
2. patch site における activation fidelity
3. 次 token 分布の変位
4. 全語彙 logit delta の単位正規化 CountSketch
5. held-out target の fingerprint separation
6. panel span に直交する random direction との separation 比較
7. target 内の glyph-label permutation null
8. cross-seed fingerprint stability
9. バランスされた標準 panel の color、shape、interaction geometry

zero-vector hook は明示的に実行する。フックのない baseline を使い回すだけでは、tensor を変更する、
dtype を変える、誤った position を操作するといった hook の不具合を検出できない。

## 主張レベル

**P0 — plumbing:** 決定論的 mock と adapter のテストが通る。

**P1 — scalar control:** 指定 RMS、実現 RMS、clipping、zero-hook no-op の確認が通る。

**P2 — reproducible fingerprint candidate:** 事前に定めた行列全体で、同一 glyph の held-out/cross-seed
fingerprint が cross-glyph/random-direction control を上回る。

**P3 — structured geometry candidate:** factor または interaction 構造が target split、direction seed、strength 間で
反復する。

**C1 — targeted causality:** 後続実験により、patch、ablation、restoration が候補効果を選択的に変化させる
component または path を特定する。

この harness は P3 までを screen できる。stage label は実行ごとに条件を満たして獲得するもので、
ソフトウェアから自動的に継承されない。標準 artifact は C1 の表現を許可しない。P2/P3 の証拠だけで
glyph の意味や機構が確立するわけでもない。

## Null と control

同梱の control は異なる失敗モードを扱い、相互に代替できない。

- neutral glyph: 一般的な glyph/emoji の存在
- panel centering: panel 全体に共通する成分
- zero hook: 介入機構自体の副作用
- random span-orthogonal direction: panel span 外の一般的な方向感度
- sign flip: 局所奇対称性と saturation
- dose grid: 単調性と clipping
- iso-KL arm: 実行した場合に限る、おおよそ等しい出力分布変位
- target 内 label permutation: target 構造を保ったままの label identity
- tokenization receipt: 生の分割と wrapper 長の不一致
- backend parity: 実装/runtime 間の不一致。glyph に対する null ではない

任意 arm を実行していないことは、負の結果ではなく証拠の欠落である。最小の permutation p 値は有限グリッド上の
screening floor であり、正確なゼロ確率ではない。

## 次段階への基準

より細かな因果実験に進む価値がある候補は、複数の target cluster、別々に推定した複数の source direction、
少なくとも 2 つの random direction、正の dose grid、明示的な scalar-balance receipt、実行と一致する capability/parity
receipt をすべて通過しなければならない。次の実験は component patching、path patching、ablation/restoration、
natural-language projection removal、checkpoint emergence、cross-model replication である。

## Phase I の出版目標

Phase I の到達点は英語論文であり、repository の英日ペアドキュメントがそれを支える。論文では、方法、
事前に定めた実験セル、異質性、負の結果、未実施の control を報告する。各 run を source、config、
runtime/dependency、model artifact、validation receipt に結び付け、事前因果的証拠と因果・意味の主張を分離する。
