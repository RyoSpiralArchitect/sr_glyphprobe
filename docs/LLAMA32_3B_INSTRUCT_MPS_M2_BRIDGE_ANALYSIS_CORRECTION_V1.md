# Llama 3.2 3B Instruct M2 bridge analysis correction v1

[日本語](LLAMA32_3B_INSTRUCT_MPS_M2_BRIDGE_ANALYSIS_CORRECTION_V1.ja.md) · [Original bridge freeze](LLAMA32_3B_INSTRUCT_MPS_M2_BRIDGE_V0.md)

Analysis ID: `glyphprobe-llama32-3b-instruct-mps-m2-bridge-analysis-v1`

## Why a versioned correction is required

All four frozen model processes completed successfully and the execution
receipt authorized analysis. The first invocation of analysis v0 then failed
closed with `Frozen config differs for primary:capture.layers`.

The failure occurred at the first panel's `resolved_config.yaml` validation.
That file correctly preserves normalized depth specifications `[0.2, 0.4]`;
the run summary separately records the resolved layers `[5, 11]`. Analysis v0
incorrectly expected `[5, 11]` in both places.

Before the failure, the analyzer reached only the public prestage authority
inputs, panel/wrapper hashes, and the primary resolved config. It had not opened
any run receipt, run summary, or intervention ledger. It produced no analysis
directory and assigned no scientific decision. P2 and retired C1 were not
accessed.

Reusing or silently editing analysis v0 is forbidden. This document and the v1
manifest freeze a new analysis version before any scientific outcome is read.

## Only correction

Analysis v1:

- validates `[0.2, 0.4]` in each stored `resolved_config.yaml`; and
- continues to require `[5, 11]` from every run summary.

The model runs, target slice, panels, score, leave-one-target-group-out
prototypes, joint stratified bootstrap, two endpoints, 20,000 replicates, seed,
practical threshold, and non-rescuing layer-11 rule are unchanged. The v1
analyzer also verifies a committed static-file manifest, the exact execution
receipt, and a clean public `main` worktree before opening outcome artifacts.

## Claim boundary

The resulting decision remains an exploratory bridge on 24 reused prestage
targets. Positive or negative output cannot establish a scale curve,
tokenizer independence, emoji semantics, causal localization, generation
behavior, or independent target generalization. No model forward occurs during
analysis, and no confirmatory P2/C1 bank is an input.
