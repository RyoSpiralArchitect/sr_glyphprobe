# T22 CPU lexical comparison: exposed-eight descriptive results

[日本語](T22_CPU_LEXICAL_RESULTS_V0.ja.md) | [Frozen protocol](T22_CPU_LEXICAL_CANARY_V0.md)

Completed on 2026-10-20 at 06:41 JST. All eight preselected exposed items,
both carriers, both fixed donors, and all four operations were retained.
These are descriptive measurements, with no hypothesis test, efficacy screen,
population confidence interval, or confirmatory verdict. The 384-item exploration
has not run and must not be selected or retuned using these eight effect signs.

## Main observation

V-only replacement changes the lexical readout in this conditioned computation.
The mean position-adjusted margin decrement is +0.001805 for V, +0.000437 for K,
and +0.000899 for KV. KV is not the sum of K and V in this comparison:
`Delta_KV - Delta_K - Delta_V` averages **−0.001343**.
The eight-item means do not establish that V dominates across the larger panel
or that V carries semantic content independently of downstream routing.

Each metric first subtracts its identical-batch-slot neutral reference. Delta
is the suffix effect minus the glyph effect, averaged over two carriers and
two donors within each target. A positive margin Delta means glyph replacement
reduces own-keyword-versus-best-competitor margin more than the matched-count
suffix replacement. The gallery is the own alias followed by the same fixed
128 source aliases; it is not a vocabulary-wide or generation metric.

| Operation | Mean adjusted margin decrement | Item sample SD | Item range | Absolute glyph margin decrement |
|---|---:|---:|---:|---:|
| Reference | 0 | 0 | 0 to 0 | 0 |
| K | +0.000437 | 0.001765 | −0.002796 to +0.002813 | +0.000193 |
| V | +0.001805 | 0.003647 | −0.003502 to +0.009042 | +0.002353 |
| KV | +0.000899 | 0.004175 | −0.007956 to +0.005689 | +0.001340 |

All three operations have six positive and two negative item contrasts.
The nonadditivity contrast has sample SD 0.001894 and range
−0.003930 to +0.001195. Repeated conditions do not increase the sample beyond
eight target items. No operation is declared a statistical winner.

| Fixed canary index | K Delta | V Delta | KV Delta | KV − K − V |
|---|---:|---:|---:|---:|
| 0 | +0.002813 | +0.001745 | +0.000627 | −0.003930 |
| 1 | +0.001724 | +0.000970 | +0.003889 | +0.001195 |
| 2 | +0.001692 | +0.002849 | +0.002592 | −0.001948 |
| 3 | +0.000255 | +0.009042 | +0.005689 | −0.003608 |
| 4 | −0.002796 | −0.003502 | −0.007956 | −0.001658 |
| 5 | +0.000268 | +0.002683 | +0.002625 | −0.000327 |
| 6 | −0.001101 | −0.001351 | −0.001487 | +0.000966 |
| 7 | +0.000642 | +0.002004 | +0.001211 | −0.001436 |

## Own keyword, competition, rank, and attention

The margin decomposition is exact at recorded float64 precision. These are
position-adjusted components, not unadjusted own-keyword cosine changes:

| Operation | Own-cosine Delta | Max-competitor-cosine Delta | Difference: margin Delta |
|---|---:|---:|---:|
| K | −0.009472 | −0.009909 | +0.000437 |
| V | +0.001094 | −0.000711 | +0.001805 |
| KV | −0.008112 | −0.009010 | +0.000899 |

Both own-keyword and competitor terms contribute to V's mean adjusted margin.
K/KV components have different directions, which makes a margin-only account
incomplete. The strongest competitor can differ across rows; its identity and
all 129 scores are retained, together with matched-donor margin and own rank.

The adjusted top-1 decrement is −0.0625 for K and KV, and zero for V.
The absolute glyph top-1 decrement has the same means. All nonzero top-1
contrast comes from index 4 (−0.5 within that item); the other seven are zero.
Thus the positive mean margin decrement must not be reported as a corresponding
top-1 loss. These are fixed-129-gallery descriptive values, not a performance
benefit or a generation result.

V-only changes no local attention weights relative to the local baseline at
the same layer input (maximum difference exactly zero). Nevertheless its
active-versus-neutral attention differs after block 22: the mean headwise
weight L1 difference is 0.008635 at block 23 and 0.028619 at block 27, averaged
over eight items, carriers, donors, and the two position groups. This directly
illustrates the downstream-query qualification. K is not pure routing and V
is not pure semantics; a reference-attention clamp would be another experiment.

## Acquisition, checks, and evidence

The original intervention arrays were reused without new intervention forwards.
The extra acquisition used 272 single-sequence alias forwards and 16 complete
stock-glyph replay forwards. All 16 complete stock tensors matched exactly.
The original nine-file model manifest was verified before and after acquisition.
The pinned BF16 CPU runtime and NumPy version were frozen before scoring.
The acquisition took 116.76 seconds after its initial manifest check, including
model loading and the final manifest check; peak process RSS was 6,015,164,416
bytes (5.60 GiB). This timing does not include the initial manifest check.

The new synthetic suite passed **16 tests, zero skips**. An independent script
without runner or Torch imports recomputed **66,048 cosines for 512 rows**,
all item contrasts and summaries, CSV alignment, and attention diagnostics.
Maximum independent cosine error was `4.6629367034256575e-15`, below the
fixed `1e-12` arithmetic tolerance. Reference effects were exactly zero;
recorded margin-decomposition error was zero. The audit does not repeat
the omitted current stock tensors or model-file checks; those remain
source-bound acquisition assertions.

- [Result receipt](../validation/t22_cpu_lexical_canary_v0/results/result.json),
  SHA-256 `87dd3ef5ad61f5c6486d5096219126b8f1775bcc258b20685878ebcad2e2ace2`.
- [Independent audit](../validation/t22_cpu_lexical_canary_v0/independent_validation.json).
- [Frozen specification](../validation/t22_cpu_lexical_canary_v0/acquisition/specification.json),
  SHA-256 `e6da21348028f8fffe6bda879336beeffcbf515e1862271dada2db6f4bf56067`.
- [Acquisition receipt](../validation/t22_cpu_lexical_canary_v0/acquisition/acquisition_receipt.json),
  SHA-256 `5bac71106134a2c5f56cbc5c8e371e5e48832e084ca233a2d020ffa7598d10b2`.
- [Byte-identical archive manifest](../validation/t22_cpu_lexical_canary_v0/archive_manifest.json).

The archive preserves aliases, row receipts, raw cosine scores, paired
contrasts, CSV, and attention diagnostics. Complete engineering-parent arrays
remain at `runs/t22_cpu_canary_v0/`; analysis still needs those files. Historical
GPU parity, codepoint-gallery controls, emoji specificity, and behavioral benefit
remain unestablished. Any larger exploration uses the frozen candidate and
fixed gallery regardless of these canary means.
