# Before asking what an emoji means, ask whether it leaves a fingerprint

[日本語](NOTE.ja.md) · [Milestone 2 results](MILESTONE2_RESULTS.md) · [Baseline results](RESULTS_V1.md) · [Research roadmap](ROADMAP.md)

An emoji looks like an unusually convenient probe for a language model. It is small, familiar, and visually distinctive. That convenience is also a trap. The moment a model reacts differently to 🟤 and 🟣, it is tempting to tell a story about brownness, purpleness, circles, or squares.

GlyphProbe begins one step earlier.

Its first question is not what an emoji means inside a model. It asks whether a direction derived from that emoji leaves a reproducible fingerprint when added to a fixed internal activation. If the intervention magnitude, source prompts, target prompts, clipping, and random controls are all sealed, does the same direction move the next-token distribution in a recognizable way on held-out prompts?

That is a smaller question, but it has sharper failure modes.

## Building the map before naming the territory

The first panel contains ten glyphs: five colors, each represented by a circle and a square. Multiple source wrappers produce an activation direction for each glyph. Those directions are centered against the panel, normalized by RMS, and added at selected GPT-2 decoder layers. The output is not interpreted token by token. Instead, the full-vocabulary logit change is compressed into a deterministic, unit-normalized fingerprint.

The design then asks whether a glyph's fingerprint is more similar to itself across held-out target prompts than it is to other glyphs or to norm-matched random directions outside the panel span. Separate wrapper subsets estimate the source direction again. A zero-vector intervention checks whether the hook itself changes anything. A dose grid and sign flip test basic local behavior.

This produces a map of repeatability before interpretation.

## Why MLX entered the experiment

The standard run contains 14,208 intervention and control records. On Apple silicon, that made MLX a practical candidate, but using the same model name in two libraries does not guarantee the same numerical experiment. The MLX path was therefore qualified against Transformers on the exact pinned GPT-2 revision, in FP32, at the same `resid_post` layers.

The qualification covers four prompt lengths and four layers. It checks token IDs, baseline activations and logits, exact zero-hook behavior, and the magnitude and direction of a fixed non-zero intervention. All 80 gates passed. In the recorded synchronized end-to-end benchmark, median latency fell from 17.52 ms with Transformers/MPS to 10.73 ms with MLX, about 1.63× faster.

That speedup belongs to this machine, software stack, model, prompt-length grid, and measurement boundary. It is useful engineering evidence, not a general law about MLX.

One later run also records why timing needs that boundary. The first matched-null A foreground process was externally interrupted after 798 rows under severe machine load: median latency was about 309 ms rather than the 10.73 ms baseline. A sealed resume completed the exact 14,208-row grid without duplicate or missing rows or errors, with zero-hook activation/logit RMS at 0; later latency returned to about 12.43 ms. This is operational provenance, not evidence about the model or a universal speed result. The P2, independent-source, and diagnostic runs completed normally.

## What the first run showed

The standard MLX run completed without recorded errors and passed all 11 readiness checks. Its median held-out fingerprint advantage was 0.608, and the median cross-seed advantage was 0.931. The source directions aligned strongly across wrapper subsets. The intended intervention magnitude was matched to numerical precision. The dose response was monotone in the reported median, sign flips were nearly antisymmetric, and the explicit zero hook was an exact no-op in the recorded metrics.

Those are encouraging properties for a candidate map.

They are not the whole result. Eleven of the 36 layer–seed–strength cells were non-positive. Every layer had a positive median, but every layer also contained at least one negative cell. The strongest single row depended on a broad random-control separation distribution, so it is not the headline. The median, positive rate, ranges, and cross-seed aggregates are more honest summaries.

The permutation screen also reached its finite floor, `1/1001`, in every cell. That is a useful exploratory flag, but it is not a multiplicity-corrected global significance result.

## The matched controls changed the picture

Milestone 2 addressed part of the tokenization warning with three null panels. Every panel has ten conditions, three raw GPT-2 tokens per symbol, and the same prespecified 9:1 panel-prefix structure as the colored shapes. This is deliberately narrower than token-identity matching: identical token IDs would decode to the same bytes and cease to be a distinct glyph input. Panel C also contains one declared semantic-near control, the nonreference red square `🟥`, because the eligible non-colored pool was one symbol short of the 27 disjoint dominant-prefix slots.

On the original 24-target exploratory matrix, the colored-shape score exceeded the median of panels A/B/C by `0.047427` at the median of 36 paired cells. Twenty-five cells were positive and 11 were nonpositive. The 48-, 32-, and 24-dimensional same-seed algebraic folds gave `0.040200`, `0.028907`, and `0.048591`. These are descriptive comparisons, not independent cells, a percent-explained estimate, or CountSketch-seed sensitivity.

The more important result came from the frozen 48-target P2 bank. At layer 2, the mean adjusted target effect was `+0.208363`, with a frozen-v1 95% interval of `[0.137463, 0.276893]` and Holm-adjusted `p = 0.00143999`. With the independently written source wrappers it was `+0.187507`, `[0.125489, 0.247659]`, `p = 0.00393996`. Both received the v1 label “robust to the prespecified matched controls.”

Layer 4 told a different story. Its primary-source estimate was `-0.0329465`, `[-0.0761085, 0.0110094]`; the independent-source estimate was `-0.086379`, `[-0.159246, -0.016917]`. Both were unresolved under the frozen rule. The result is therefore mixed and layer-specific, not a global success.

## Auditing the analysis after the result

The v1 analyzer checks the frozen target bank, model cell, condition grids, target sampling unit, and hypothesis family. But it assigns primary and null roles from command-line order. A separate binding audit was needed to prove that all 14 published run directories—the 12 core exploratory, P2, and independent-source arms plus two diagnostics—actually map to the intended frozen configs, panels, sources, targets, paths, and hashes. That audit passed.

There is a second qualification. The v1 interval resamples target effects after the leave-one-group-out prototypes have been built once. It does not rebuild those data-dependent prototypes inside each bootstrap replicate. A post-hoc sensitivity analysis did rebuild all prototypes jointly. For the primary source, its intervals were `[0.099930, 0.295380]` at layer 2 and `[-0.099995, 0.041902]` at layer 4. For the independent source they were `[0.104210, 0.271322]` and `[-0.185084, 0.007648]`.

Those wider intervals are useful, but the method was specified after P2 outcomes were available. It assigns no p-value or confirmatory status and does not overwrite v1. The [technical result](MILESTONE2_RESULTS.md) keeps the two inferential layers separate.

The two secondary token-structure diagnostics also completed. Each covered 14,208 rows with zero errors, zero-hook activation/logit RMS of 0, and readiness 11/11. Their random-adjusted headline `emoji_fingerprint_advantage` values were `+0.751225` for the suffix-matched panel and `+0.601038` for the prefix-homogeneous panel. Those headline values are not the raw separation scores used for the paired comparison.

At CountSketch dimensions 96, 48, 32, and 24, the median standard-minus-suffix raw separation was `+0.002624`, `+0.009473`, `+0.004026`, and `+0.009700`. The corresponding standard-minus-prefix values were `+0.022096`, `+0.023254`, `+0.011040`, and `+0.025387`. At 96 dimensions, 20/36 suffix cells and 25/36 prefix cells were positive. These are post-hoc descriptive diagnostics, not inferential or equivalence tests. The lower-dimensional results are same-seed algebraic folds, not independent reruns or seed sensitivity.

## What we can say—and what we cannot

We can say that, in one pinned GPT-2 FP32 MLX `resid_post` cell, layer 2 retained a positive excess over three prespecified token-count and prefix-panel matched controls under two source-wrapper constructions according to the frozen v1 rule. Layer 4 did not pass that rule.

We cannot call this a tokenization-free glyph effect. We cannot say that GPT-2 has a brown-circle concept, that a particular attention head or MLP implements a glyph feature, that the direction carries human-readable meaning, or that the result generalizes to another model. The independent-source arm reuses the same targets and is not independent model or target replication. The completed secondary diagnostics narrow two token-structure questions descriptively; they do not establish equivalence or remove tokenization from the claim.

The summary boundary remains machine-readable: `causal_claim_authorized` is `false`. The C1 causal holdout has not been passed to a model or outcome analysis.

## What comes next

Operational Milestone 2 is complete. Layer 2 can now enter the design of a new frozen targeted causal protocol using untouched C1; layer 4 remains unresolved and is not a candidate. This permits protocol design, not a causal claim.

C1 stays closed until the candidate, intervention site and operation, endpoint, controls, and multiplicity family are fixed in a sealed patch–ablate–restore protocol. Independent backend and model or tokenizer replication also remain open. Final-paper confirmatory wording and any replication used to support it must prospectively bind scientific roles to frozen inputs and account for data-dependent prototype resampling.

Phase I still ends with an English paper, whether the final pattern is positive, mixed, or negative. That paper must show layer 2 and layer 4 together, distinguish frozen-v1 inference from post-hoc sensitivity, report the completed diagnostics with their descriptive boundary, and connect every statement to a sealed artifact. The first map has become sharper. It has also become harder to overread, which is exactly what the controls were for.
