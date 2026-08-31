# T16 operational semantics and causal subspace

T16-OSC asks two narrower questions that the T14/T15 distributional results
could not answer. First, do frozen instruction-tuned models choose the
experimenter-assigned word for an emoji and classify a matching versus
mismatching emoji-word pair? Second, does the part of the T15-B interaction
direction that is orthogonal to frozen structural nuisances causally move the
model's mismatch log odds?

## Claim boundary

The behavioral tasks are two-alternative forced choices. Passing them supports
operational association and congruence judgment only. It is not unrestricted
semantic understanding or general natural-language contradiction detection.
The causal task uses the positive T15-B Mistral cell and is therefore an
outcome-informed mechanistic follow-up. Passing it supports a causal effect of
a source-defined residual subspace on one frozen endpoint; it does not identify
a unique or complete circuit.

## Behavioral lane

The panel contains eight new axes that do not reuse the T15-A or T15-B axis
labels. Gemma 2 2B IT and Mistral 7B Instruct v0.3 are evaluated with their
native chat templates. `A` and `B` must each be exactly one next token in both
tokenizers before the final execution freeze.

The meaning task has 128 rows per model: eight axes, two emoji poles, four
prompt templates, and two answer mappings. The congruence task has 256 rows per
model after adding both word poles. The endpoint is the correct answer logit
minus the incorrect answer logit. The semantic axis, not a prompt row, is the
principal unit.

For each of the four model-task cells, the median prompt score is computed per
axis. The frozen gate requires the 20,000-replicate axis-bootstrap median lower
bound to exceed zero and the exact one-sided eight-axis sign-flip p-value, using
mean axis effect as its statistic, to be at most 0.0125. All four cells must
pass.

## Causal residual-subspace lane

The source arrays are the hash-bound Mistral T15-B directions at normalized
depths 0.875 and 1.0. For every true interaction direction, the nuisance span
contains the seven same-emoji-axis cross-axis interactions plus the emoji and
word main effects from the same source order and held-out wrapper fold. A thin
SVD projects the true direction into nuisance and residual components.

Components are averaged over both source orders and all four held-out wrappers
within each T15-B axis. Full, residual, and nuisance projection use the same
full-direction RMS scale, so residual plus projection restores the full vector
before any forward pass. Each of the seven cross-axis controls is independently
unit-RMS scaled.

The frozen targets are 128 counterbalanced mismatch judgments on the T15-B
panel. At each of two registered depths, the runner measures zero, positive and
negative full, residual, and projection interventions, and positive and
negative interventions for all seven cross-axis controls. The primary endpoint
is mismatch logit minus match logit. The three primary estimands are:

1. full directional antisymmetry minus the median cross-axis control;
2. residual directional antisymmetry minus the median cross-axis control;
3. full directional antisymmetry minus projection-only antisymmetry.

All three pooled-depth axis-level estimands must have bootstrap median lower
bounds above zero and exact sign-flip p-values, using mean axis effect as the
test statistic, at most 0.05/3. The zero hook and vector restoration are
engineering gates. No favorable depth, axis, template, or control may be
selected after outcomes.

## Execution boundary

Tokenizer and artifact preflight performs zero model forwards. The final
manifest must be committed before model loading. The runner uses only pinned
local snapshots, never generates text, checks the furnace for foreign GPU work
before each phase, and exits with code 75 rather than contending. Raw ledgers
remain in furnace scratch storage; compact analyses and receipts may be
committed after both behavior roles or the complete causal run pass audit.
