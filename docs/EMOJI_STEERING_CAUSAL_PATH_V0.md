# Emoji Steering Causal Path v0

[Japanese / 日本語](EMOJI_STEERING_CAUSAL_PATH_V0.ja.md) ·
[T14-X expansion](EMOJI_STEERING_SPECIFICITY_EXPANSION_V0.md) ·
[Scientific contract](SCIENTIFIC_CONTRACT.md)

Protocol ID: `glyphprobe-emoji-steering-causal-path-v0`  
Experiment label: **T14-C**

## Causal question

T14-C asks a deliberately narrower question than “does the model understand an
emoji?” It asks whether one fixed downstream Transformer component selectively
mediates the late structured-source output-distribution effect, relative to
signed directions drawn from the same source residual covariance.

The cell is fixed before T14-X outcomes: Llama 3.2 3B base, BF16,
Transformers/CUDA, a unit-RMS intervention of magnitude 0.25 at `resid_post`
block 23 (normalized depth 0.875), and next-token Jensen–Shannon divergence as
the sole primary endpoint.

## Two-stage separation

The protocol separates component selection from causal confirmation.

1. **Localization:** use the 32 already public targets to compare eight fixed
   downstream candidates: `attn_out` and `mlp_out` in blocks 24–27. A block-24
   `resid_pre` patch is the positive erasure control and block-22 `mlp_out` is
   the upstream temporal sham.
2. **C1 v2 confirmation:** bind exactly one eligible candidate by the frozen
   selector, commit and push that binding, and only then materialize a new
   192-target bank. The bank is not generated during localization.

The selector always chooses the eligible candidate with the largest median
target-level structured-minus-null necessity excess, with a fixed lexical site
order as the tie-break. A negative score does not trigger a new search: the
highest-ranked eligible site is still bound and carried into C1 v2. If no site
passes engineering fidelity, the experiment fails closed before generating the
bank.

## Interventions and controls

Each target receives 80 signed treatment conditions:

- 24 leave-one-wrapper-out glyph-system prototypes × two signs; and
- 16 source-covariance nulls × two signs.

For each treatment and candidate component, four model passes are retained:

- ordinary treatment;
- **necessity:** replace the treatment component with its paired baseline value;
- **sufficiency:** patch the treatment component value into the baseline path;
- **restoration:** replace the treatment component with the captured treatment
  value to verify the patch round trip.

Each condition batch also carries two identical zero-vector rows. Their logits
are compared within the same batch as the explicit-zero hook check; they do not
enter the 80-condition scientific estimands.

Localization therefore contains 25,600 response records. The one-site C1 v2
confirmation contains 15,360 records over 192 new target prompts.

## Primary C1 v2 decision

The principal sampling units are the 192 targets, stratified as 12 groups of
16. Glyph systems, wrapper folds, signs, and null seeds are repeated measures
inside each target.

The primary result is one intersection–union test requiring all three
target-level estimands to pass. Each condition family is first reduced within
target, and the fixed population aggregate is the median across all 192
targets:

1. structured treatment minus signed-null treatment: JS lower bound > 0.002;
2. structured necessity drop minus signed-null necessity drop: lower bound >
   0.0005; and
3. structured sufficiency minus signed-null sufficiency: lower bound > 0.0005.

Uncertainty uses a two-sided equal-tailed 95% interval from 20,000 stratified
target-cluster bootstrap replicates. Each component also requires a one-sided
99,999-draw paired target sign-flip p-value against zero below 0.05. Because all
three components form one intersection–union claim in one model and one site,
no additional multiplicity correction is used. The restoration, explicit-zero,
and upstream-sham gates must also pass.

If any component fails, T14-C is negative. Another site, endpoint, subset,
sign, source form, depth, or model cannot rescue it.

## Holdout boundary

The retired C1 v1 bank, P2 bank, and public prestage targets cannot be used as
C1 v2. The deterministic C1 v2 generator is frozen before localization, but it
may emit no prompt rows until the selected-site manifest and causal executable
hashes are committed and pushed. During materialization, only row count,
stratum counts, SHA-256, and the receipt are surfaced; prompt bodies remain
unprinted until the one-shot C1 v2 execution is complete.

## Frozen execution order

The executable exposes the gates in this order:

1. `audit-design`, `write-design-preflight`, `freeze`, then `audit-freeze`;
2. `run-localization` and `validate-localization` on the public targets;
3. `select-site`, followed by committing and pushing the resulting manifest;
4. `materialize-bank`, which fails unless `HEAD == origin/main` for all protected
   causal files;
5. `run-confirmation`, `validate-confirmation`, and finally
   `analyze-confirmation`.

Localization and confirmation outputs are external, atomic, hash-bound site
directories. Execution checks furnace contention before model load, each site,
and each target; exit code 75 is a resumable yield, not scientific evidence.

## Authorized conclusion

A passing IUT may establish that the selected component causally mediates the
operational structured-versus-null next-token JS effect in this pinned cell.
It does not establish emoji meaning, understanding, a complete circuit,
natural encoding strength, generated behavior, tokenizer independence, scale,
architecture or model-population generality, or independent replication.
