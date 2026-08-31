# T16 distributed late-band mediation

T14-C found that a prospectively selected single downstream component did not
pass treatment, necessity, and sufficiency together. T16-DP tests one bounded
alternative: the effect may be distributed across the complete late
attention-plus-MLP band rather than localized to one module.

## Frozen intervention

The model, source directions, injection site, magnitude, endpoint, and nulls
are unchanged from T14-C. Llama 3.2 3B receives the T14 treatment at the output
of block 23. The mediator is the joint ordered set of `attn_out` and `mlp_out`
at every block from 24 through 27, eight components total. The whole band is
fixed before outcomes; no component is ranked or removed.

For every condition batch, one treatment pass captures all eight components.
Necessity replaces all eight treatment-run components with their baseline
captures. Sufficiency injects no source vector and replaces all eight baseline
components with the treatment captures. Restoration repeats the treatment and
reinstates the captured treatment components. Replacements preserve their
natural block order.

## Fresh targets and decision

A deterministic 192-row, 12-stratum target bank is materialized outside Git
only after the final freeze commit is pushed. Its prompt bodies are not printed
to the research transcript. Materialization rejects any exact overlap with the
deterministically reconstructed T14 C1 v2 bank or the public localization bank.

The three target-level estimands are structured-minus-null treatment JS,
necessity-drop JS, and sufficiency JS. A three-component intersection-union
test requires every 20,000-replicate stratified-bootstrap lower bound to exceed
its frozen practical floor and every one-sided 99,999-draw sign-flip p-value to
be below 0.05. Restoration, within-batch zero, and the already-bound T14
upstream-sham evidence are additional gates.

## Claim boundary

A pass supports joint mediation by this complete late band in one pinned model
and operational endpoint. It does not show that all eight components are
individually necessary, that the band is minimal, or that it is a unique or
complete emoji circuit. A failure closes this frozen distributed-band attempt;
it may not be rescued by selecting a subset, site, sign, target stratum, or
alternative endpoint from the same bank.

