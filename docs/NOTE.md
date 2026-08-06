# Before asking what an emoji means, ask whether it leaves a fingerprint

[日本語](NOTE.ja.md) · [Technical results](RESULTS_V1.md) · [Research roadmap](ROADMAP.md)

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

## What the first run showed

The standard MLX run completed without recorded errors and passed all 11 readiness checks. Its median held-out fingerprint advantage was 0.608, and the median cross-seed advantage was 0.931. The source directions aligned strongly across wrapper subsets. The intended intervention magnitude was matched to numerical precision. The dose response was monotone in the reported median, sign flips were nearly antisymmetric, and the explicit zero hook was an exact no-op in the recorded metrics.

Those are encouraging properties for a candidate map.

They are not the whole result. Eleven of the 36 layer–seed–strength cells were non-positive. Every layer had a positive median, but every layer also contained at least one negative cell. The strongest single row depended on a broad random-control separation distribution, so it is not the headline. The median, positive rate, ranges, and cross-seed aggregates are more honest summaries.

The permutation screen also reached its finite floor, `1/1001`, in every cell. That is a useful exploratory flag, but it is not a multiplicity-corrected global significance result.

## The tokenization warning

All ten primary glyphs are three GPT-2 tokens long, which removes one obvious imbalance. It does not remove tokenization as an explanation. The token sequences are distinct, the blue circle has a different middle-token pattern, and the neutral `·` control is only one token long.

So the current experiment cannot separate a visual or semantic glyph factor from every property of its token sequence. A cleaner follow-up needs token-length- and prefix-matched controls. This is not a footnote to hide after a positive graph; it is one of the main design constraints for the next experiment.

## What we can say—and what we cannot

We can say that, under one pinned GPT-2 FP32 `resid_post` setup, the tested glyph-derived directions produced a reproducible output-fingerprint candidate relative to the bundled controls.

We cannot yet say that GPT-2 has a brown-circle concept, that a particular attention head or MLP implements a glyph feature, that the direction carries human-readable meaning, or that the effect will replicate in another model. We also have not tested sequence generation, SAE features, iso-KL matching, or path-level causality.

The summary file makes this boundary machine-readable: `causal_claim_authorized` is `false`.

## The next experiment

The next step is not to add more adjectives to the current result. It is to make the candidate easier to falsify.

That means matched tokenization controls, a frozen confirmatory target set, a small prespecified hypothesis family, and inference at the target-prompt cluster level. It means patching, ablating, and restoring candidate components or paths. It also means repeating the confirmatory cell through another internal backend and in at least one additional model or tokenizer.

Phase I ends with an English paper, whether the final result is positive, mixed, or negative. The standard for that paper is not a dramatic visualization. It is a chain of claims that each point back to a sealed config, receipt, raw artifact, and falsification test.

The current run is the first map in that chain.
