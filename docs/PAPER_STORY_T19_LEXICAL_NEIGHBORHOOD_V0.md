# T19 paper story: broad lexical readout and a bounded mechanism test

[日本語](PAPER_STORY_T19_LEXICAL_NEIGHBORHOOD_V0.ja.md) · [Manuscript package](../paper/README.md) · [T19 results](T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0_RESULTS.md) · [Frozen protocol](T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.md) · [T18 precursor](PAPER_STORY_T18_FRESH_LEXICAL_V0.md)

Status: **paper spine and claim table frozen; anonymous compact artifact and
fresh-eyes review complete; OpenReview upload not performed**.

Draft v0 now defines `T19-L` and `T19-C` at first use. Its Appendix A records
the compact decision lineage from the early steering and tokenization screens
through T18, while keeping exploratory, failed-confirmation, and T19 primary
evidence separate.

## Candidate title

> **Beyond Short Names: Emoji Keyword Retrieval across Models and a Bounded Late-Component Test**

## One-sentence contribution

Raw atomic emoji retrieved lexically disjoint CLDR keyword aliases better than
literal codepoints in all nine prespecified model/tokenizer configurations after exact
four-view token-count matching, yet a preregistered rank-8 `attn_out`/`mlp_out`
intervention on 192 emoji held out from T19-L found no primary site that was
both necessary and sufficient. Their surfaces may have appeared before T19.

That positive observational result and negative causal result belong together.
The paper centers the separation between a broad, repeatable lexical readout
and an unsupported prespecified sparse late-component explanation. It makes no
claim that emoji have general-purpose meaning vectors.

## Why T19 changes the T18 story

T18 established that repository-fresh composite emoji retrieve official short
names better than codepoint literals. A skeptical reader could still say that
the probe had rediscovered a standardized label string. T19 replaces that
endpoint with a CLDR keyword whose words do not overlap the official name.
Every prespecified configuration remains positive in both unrestricted and token-count-matched
analysis. The relation is therefore wider than official-label lookup.

The new symbol control keeps the next claim narrow. Official-name retrieval is
also present for many non-emoji Unicode symbols, so “emoji alone become words”
is too strong. Keyword breadth is much smaller for the prespecified symbol
panel, and emoji-minus-symbol point estimates are positive in all nine
configurations. This is
a specificity clue, not a registered proof of an emoji-only faculty.

## The result has three layers

### 1. Confirmed lexical breadth

The `r = 3 of 4` core primary passed at `p = 0.0027`, with all four core cells
positive. In fact, all nine configurations passed both tokenization components
and the registered effect-size floor. A separate validator, which does not
import the acquisition analyzer, reconstructed all 36 randomization tests and
the complete raw-to-summary evidence chain.

This is the strongest new paper claim: under fixed text inputs and retrieval
endpoints, atomic emoji index more than one exact name string.

### 2. Bounded emoji–symbol contrast

Across models, the mean emoji alias effect was about four to seven times the
symbol mean, depending on the component. Canonical names remained stronger
than aliases, especially for symbols. The observational picture is therefore
graded:

```text
official name retrieval
    broad across emoji and named symbols

disjoint keyword retrieval
    robust across the prespecified emoji configurations
    smaller and model-heterogeneous for symbols
```

Because symbol category, frequency, label quality, and token identity are not
fully matched, this belongs in the paper as a boundary result rather than a
standalone semantic claim.

### 3. Negative simple-mechanism test

T19-C used a separate 128-item source bank and a 192-item evaluation bank.
Zero hooks and restoration were exact at all six sites. The primary block-24
`attn_out` and `mlp_out` tests nevertheless failed: adjusted necessity and
sufficiency effects were near zero and did not pass the practical or
intersection-union requirements.

The secondary block-27 MLP result is revealing precisely because it is
incomplete. Its learned patch was more effective than the random patch, while
learned-coordinate removal was not harmful. Three of the composite endpoint's
15 additional correct contrasts came from keyword gains; 12 came from lost
codepoint self-retrieval. This disruption can move the endpoint without
identifying its required mediator. It motivates distributed and nonlinear
accounts without confirming one.

## Suggested paper structure

1. **Threat model.** Separate raw Unicode surface, official label, lexical
   neighborhood, literal encoding, and rendered perception.
2. **Prospective design.** Explain CLDR source binding, lexical disjointness,
   three banks, token-count strata, and the single causal admission gate.
3. **Cross-model observational primary.** Lead with 4/4 core and 9/9 total
   cells, then show exact matched coverage and independent reconstruction.
4. **Named-symbol boundary.** Show official versus alias retrieval and the
   emoji-minus-symbol profiles without upgrading the secondary comparison.
5. **Causal falsification.** Present exact engineering controls, both negative
   primary sites, and the asymmetric block-27 MLP secondary result.
6. **Interpretation.** A readable aggregate lexical relation need not be a
   single shared manifold or low-rank late mediator.
7. **Limitations and next tests.** Human-rated aliases, token-identity controls,
   distributed multi-site interventions, nonlinear readouts, and genuinely
   independent model populations.

## Figure plan

- **Figure 1:** crossed design—emoji/symbol × canonical/alias/codepoint—and the
  observational/source/evaluation bank split.
- **Figure 2:** nine-model unrestricted and matched emoji effects with the
  `0.02` floor; visually mark the four core cells.
- **Figure 3:** emoji versus symbol alias and canonical profiles, explicitly
  labeled secondary.
- **Figure 4:** six-site necessity–sufficiency plane with engineering status;
  primary block-24 sites highlighted.
- **Appendix:** depth trajectories, exact token strata, all condition metrics,
  source/evaluation hashes, and independent validators.

## Claim table for manuscript freeze

| Candidate claim | Evidence | Boundary |
|---|---|---|
| Atomic emoji retrieve disjoint CLDR keywords better than codepoint literals in at least 3/4 core cells | supported; 4/4, partial conjunction p=0.0027 | frozen late window and endpoints |
| The result survives exact four-view token-count matching | supported; 9/9 cells pass both components | not token identity or tokenizer independence |
| T18 was only official-label lookup | disfavored | CLDR keyword may still co-occur in training |
| Alias breadth is larger for emoji than symbols | 9/9 positive point estimates | registered secondary; control panels are not fully exchangeable |
| Block-24 rank-8 `attn_out` or `mlp_out` is a necessary-and-sufficient mediator | unsupported | one Llama cell and one intervention family |
| Block-27 MLP is a causal mechanism | unsupported | sufficiency positive, necessity negative, secondary only |
| Models visually perceive or humanly understand emoji | unauthorized | Unicode text input only |
| One universal emoji manifold or scale law exists | unauthorized | model-private trajectories and confounded model roster |

## Best next experiments

The next work should test explanations, not add another large emoji panel.

1. Human-rate a smaller alias/paraphrase set for synonymy, specificity, and
   familiarity, then freeze it before tokenization outcomes.
2. Build tighter symbol controls within Unicode category and lexical-frequency
   bands; treat token identity, not only token count, as a design variable.
3. Test distributed multi-site removal across a frozen late band. The current
   result makes a one-site rank-8 search less attractive, not more.
4. Compare linear cross-covariance with nonlinear or sparse readouts on a new
   source/evaluation split, without reusing T19-C to choose the winning method.
5. Preserve the block-27 asymmetry as a registered prediction: transport may be
   possible without necessity because the lexical relation is redundant.

## Writing boundary

Prefer “lexical correspondence,” “CLDR keyword neighborhood,” “token-count
matched,” “registered causal negative,” and “distributed or redundant remains
possible.” Avoid “semantic understanding,” “emoji concept vector,” “visual
recognition,” “universal circuit,” “causal localization succeeded,” and
“tokenizer-independent.”
