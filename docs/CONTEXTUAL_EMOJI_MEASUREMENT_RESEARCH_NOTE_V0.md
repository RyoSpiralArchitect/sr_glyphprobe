# Contextual cue interactions and response-choice stability

[日本語](CONTEXTUAL_EMOJI_MEASUREMENT_RESEARCH_NOTE_V0.ja.md) · [Next study options](CONTEXTUAL_EMOJI_MEASUREMENT_NEXT_PLAN_V0.md)

**Public-integration note, October 26, 2026:** this dated note retains the original
study status. References to excluded handoffs, notebooks, specifications or
runtime records concern the author's local archive; the public checkout does
not supply a complete historical run. See the
[public integration scope](PUBLIC_INTEGRATION_SCOPE_20261026.md).

Research note, 2026-10-07 (JST). Status: **post-hoc, descriptive development analysis**. This note prepares a paper addition; it does not revise the submitted paper or introduce a confirmatory endpoint. All new calculations use saved scores on a local Mac CPU. No model forward, tokenizer call, GPU job, or new stimulus acquisition is part of this analysis.

## 1. The contribution taking shape

The most defensible finding is a separation within the output measurement itself:

> In this development inventory, context-by-cue interactions persist across three tested response formulations while preferred response polarity changes frequently.

The study makes a concrete methodological distinction among an interaction, a reversal of the cue-replacement effect, and selection of the author-intended continuation in all four inputs. These properties impose increasingly strong conditions on the same four scores. An exact decomposition explains how they can diverge. Their divergence is an empirical result worth preserving, even if the later causal study returns a negative result.

The scientific question has sharpened from “does an emoji contain meaning?” to “how does a contextual cue affect an ordinary output probability, and which additional evidence would establish a reliable interpretation or an output-linked causal contribution?” This is an operational refinement, not a claim to have identified semantic understanding.

### How the evidence connects

| Study, using descriptive names | Measured quantity | Evidence ceiling |
| --- | --- | --- |
| Cross-model lexical retrieval | Hidden-state retrieval of word-disjoint CLDR keywords against codepoint views | Lexical readability in the specified model/item configurations |
| Low-rank late-component tests | Registered necessity-and-sufficiency contrasts; optimized follow-up calibration | Tested rank-8 account unsupported; primary optimized sites uncalibratable |
| Conditional attention-message test | Glyph-position disruption/restoration after readout-state replacement | Conditional cosine-margin contribution; signed mean top-1 effects of unadjusted glyph-message decrement and restoration remain zero |
| Contextual output pilot and word controls | Full-continuation likelihood under crossed goals and cues | Ordinary output-score interaction on authored development scenarios |
| Candidate-formulation sensitivity and this note | The same output scores across three response pairs | Separation of interaction, effect crossover, and response-choice stability |

The populations, interventions, and endpoints differ across rows. The earlier attention path has **not** been shown to carry the present output effect. Earlier lexical p-values, causal verdicts, and zero top-1 effects retain their original scope. See the [experiment guide](../paper/EXPERIMENT_GUIDE.md) and [post-review evidence report](POST_REVIEW_EVIDENCE_RESULTS_V0.md).

## 2. What was actually measured

The output studies use Llama 3.2 3B base in BF16, with 24 author-written scenarios in six recurring families. Each scenario crosses two goal contexts with two cues. The word study uses alternatives recorded before its scores were acquired. All studies score complete teacher-forced continuations; they do not sample free responses, use a CLDR target, replace a readout state, or intervene in a hidden component.

The three candidate pairs are:

1. The original, scenario-specific pair.
2. ` This meets my goal.` / ` This does not meet my goal.` (5 / 7 tokens).
3. ` This is suitable for my goal.` / ` This is unsuitable for my goal.` (7 / 8 tokens).

The leading space is part of each new continuation. Positive/negative wording maps to the original A/B polarity, preserving the recorded orientation. The two additional pairs were specified **after** the original results. They change vocabulary, specificity, morphology, and length together. Their equivalence has not been independently established.

### Inventory and unit of analysis

| Inventory | Completed / planned | Interpretation |
| --- | ---: | --- |
| Original emoji scores, including absent cue | 288 / 288 | 192 crossed + 96 absent scores |
| Original word-control scores | 192 / 192 | Same 24 scenarios |
| Two additional pairs, both carriers | 768 / 768 | Repeated measurements of the same scenarios |
| Unique scientific condition/continuation scores | **1,248 / 1,248** | 1,152 crossed + 96 original absent |
| Four-score decomposition tables | 144 / 144 | 24 scenarios × 2 carriers × 3 pairs; each score is an A/B log-probability difference |
| Historical parity repeats | 384 / 384 | Engineering checks, excluded from scientific sample size |

There are 24 development scenarios, six repeated families, and repeated cue pairs. There are neither 72 independent scenarios nor 1,248 independent experimental units. The new analysis reports finite-inventory summaries without population p-values or confidence intervals. No new absent-cue scores exist for the two additional pairs.

## 3. The complete result, before interpretation

H is the author-oriented difference of cue-replacement effects across contexts, in nats. “Aligned” means the higher-scoring candidate agrees with the author's recorded label. It is not human-validated accuracy.

| Pair | Carrier | Mean H | H > 0 / 24 | Expected effect crossover / 24 | Aligned inputs / 96 | All four aligned / 24 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Original | Emoji | 1.3123 | 23 | 12 | 54 | 0 |
| Original | Word | 2.2505 | 23 | 18 | 60 | 3 |
| Explicit negation | Emoji | 1.1960 | 19 | 10 | 54 | 2 |
| Explicit negation | Word | 1.6120 | 22 | 18 | 62 | 4 |
| Adjective pair | Emoji | 1.3160 | 24 | 14 | 55 | 2 |
| Adjective pair | Word | 2.3119 | 24 | 19 | 60 | 5 |

All pairs and negative cases remain included. The equal-pair mean H is 1.2748 for emoji and 2.0581 for words, a descriptive average rather than a newly designated primary endpoint. Word-minus-emoji mean H is +0.9383, +0.4160, and +0.9958 across the three pairs.

### Stability requires tracking the same inputs

| Property across all three pairs | Emoji | Word |
| --- | ---: | ---: |
| Positive H in every pair | 19 / 24 | 22 / 24 |
| Expected effect crossover in every pair | 6 / 24 | 13 / 24 |
| All four inputs aligned in every pair | **0 / 24** | **0 / 24** |
| Input aligned in every pair | 26 / 96 | 31 / 96 |
| Input misaligned in every pair | 18 / 96 | 9 / 96 |
| Input polarity varies across pairs | **52 / 96** | **56 / 96** |
| Original ↔ explicit-negation polarity flips | 36 / 96 | 36 / 96 |
| Original ↔ adjective polarity flips | 31 / 96 | 34 / 96 |
| Explicit-negation ↔ adjective polarity flips | 37 / 96 | 42 / 96 |

The last three rows overlap; they must not be summed as distinct inputs. Similar overall alignment totals conceal substantial changes in which inputs align. Even among scenarios with positive H in every pair, polarity changes occur in 13/19 emoji scenarios and 19/22 word scenarios. No score ties or zero H values occur in these data.

## 4. Why interaction and choice can separate

For a fixed scenario, carrier, and candidate pair, let

\[
s(c,v)=\log P(A\mid c,v)-\log P(B\mid c,v),\qquad t(c,v)=\eta s(c,v),
\]

where the recorded orientation is \(\eta\in\{-1,+1\}\). Code context p/q as \(C=-1,+1\), and cue a/b as \(V=-1,+1\). The four observed values have the exact representation

\[
t(C,V)=b_0+b_C C+b_V V+b_{CV}CV,
\qquad b_k=\tfrac14\sum_{C,V} f_k(C,V)t(C,V),
\]

with \(f_k\in\{1,C,V,CV\}\). This is a change of coordinates on four scores, not an identified decomposition of neural computation.

The oriented cue-replacement effects are

\[
\eta\Delta_p=2(b_V-b_{CV}),\qquad
\eta\Delta_q=2(b_V+b_{CV}),\qquad H=4b_{CV}.
\]

The author-aligned margin for each input is \(m(C,V)=CV\,t(C,V)\). Consequently:

| Requirement | Exact condition | What it checks |
| --- | --- | --- |
| Positive interaction | \(b_{CV}>0\) | Direction of the interaction contrast |
| Expected effect crossover | \(b_{CV}>\lvert b_V\rvert\) | Cue replacement reverses direction between contexts |
| All four candidates align | \(\min_{C,V}m(C,V)>0\) | Every absolute candidate preference has the authored polarity |

All-four alignment implies the expected crossover, which implies positive H. The reverse implications fail. Ties fail these strict conditions.

Also, \(\sum m=H\), so mean author-aligned log margin equals **H/4**. Reporting this mean as independent corroboration would count the same information twice.

Changes in the table-wide offset \(b_0\) or context main effect \(b_C\) can move absolute preferences without changing H. Changes in \(b_V\) can also affect crossover. These identities make the observations intelligible. They do not identify the offset as a pretrained candidate “prior,” nor attribute changes to length, negation, or familiarity. A candidate effect that interacts with context and cue can still affect H.

### A concrete, explicitly post-hoc illustration

For `affect_02` with emoji, H is 4.7005, 4.3103, and 4.2488 across the three pairs. The smallest author-aligned margin changes from −0.4351 to +0.5805 and +0.7242. The interaction stays large while the strict four-input criterion changes. This scenario illustrates the distinction; it was selected after observing the results and is not a confirmatory causal target.

## 5. What the additional CPU diagnostics can establish

The [reproducible analyzer](../scripts/analyze_contextual_emoji_measurement_v0.py) reconstructs every table from hash-bound saved data. Its [receipt](../validation/contextual_emoji_measurement_v0/analysis.json) retains scenario-level decompositions, all pairwise transitions, descriptive margin-threshold checks, and leave-one-family-out summaries. The [executed companion notebook](../notebooks/contextual_emoji_measurement_v0.ipynb) presents the bounded summaries and verifies the arithmetic again.

Across the six carrier-by-pair comparisons, the mean absolute change in \(b_0\) ranges from 1.3491 to 1.9992 nats; that in \(b_{CV}\) ranges from 0.1183 to 0.2158. Thus the observed response offset moves substantially more than the interaction coefficient on this scale. The orthogonal decomposition of squared score changes is an accounting identity. Its component shares describe score movement, **not fractions of a causal explanation** for choice flips.

Margin-threshold tables check how many flips remain when both formulations' absolute margins exceed specified descriptive thresholds. At a threshold of 1 nat in both pairs, emoji flips remain in 7/30, 15/52, and 9/34 eligible inputs for original–negation, original–adjective, and negation–adjective comparisons; word counts are 5/16, 10/43, and 6/19. The finite data therefore include flips beyond near-zero ties. These thresholds were chosen after acquisition; they do not define an eligibility filter.

All 36 leave-one-family-out mean H values remain positive. The six-omission ranges are 1.0792–1.5309, 1.0080–1.3769, and 1.1216–1.4989 for emoji; 1.8249–2.5758, 1.3965–1.8806, and 1.9013–2.5924 for words, in the same pair order. This shows finite-inventory sensitivity, not six independent replications or a generalization guarantee.

Saved per-token log probabilities permit an additive split at the longest common token prefix of A and B within each input. This can distinguish shared-prefix numerical differences from the remaining score contrast. It provides neither cross-formulation semantic token alignment nor localization to an internal neural component. Whole-sequence scores remain the reported endpoint.

### Open computational-consistency issue

Shared-prefix score residuals are nonzero in **355/576 paired inputs**, with maximum absolute prefix log-score difference **0.187710 nats** and maximum absolute prefix contribution to H **0.175653**. In a causal autoregressive model, an identical conditioning prefix should define the same next-token distribution; separate full-sequence executions can introduce numerical dependence on execution shape, but that source has **not** been isolated here. Historical exact replay tests repeat the same executions and do not test this cross-length property.

All 355 nonzero cases occur among 520 unequal-length candidate pairs; all 56 equal-length pairs have zero residual. A source-code audit found correct preceding-token indexing and FP32 `log_softmax`, with causal masking delegated to the pinned model implementation. The latter was not independently executed or audited here. Residuals predate weight staging. Length/shape dependence is a plausible lead, not an identified BF16 cause.

Splitting saved scores into prefix and remaining tail preserves score and H additivity. None of the 144 H signs changes when inspecting the tail contribution alone. Absolute preference changes in 1/576 inputs, crossover in 2/144 tables, and all-four alignment in 1/144 tables; all affected cases use emoji. The notebook independently recomputes these counts. This bounds one descriptive sensitivity; it does not validate numerical accuracy or justify replacing the endpoint. Keep the original scores and pin a small computational-consistency check before further mechanistic acquisition or a definitive paper integration. The [next plan](CONTEXTUAL_EMOJI_MEASUREMENT_NEXT_PLAN_V0.md) puts this gate first.

## 6. Absent-cue subtraction answers a different question

For the original pair only, define

\[
s_{\mathrm{relative}}(c,v)=s(c,v)-s(c,\mathrm{absent}).
\]

The same absent prompt is shared across the two carriers. This subtraction changes \(b_0\) and \(b_C\), while \(b_V\), \(b_{CV}\), H, and the cue-effect crossover remain unchanged. The cancellation is exact algebra, not a hypothesis awaiting further model data.

| Original pair | Raw alignment / 96 | Cue-relative alignment / 96 | Sign changes / 96 | Raw → relative all-four / 24 |
| --- | ---: | ---: | ---: | ---: |
| Emoji | 54 | 62 | 32 | 0 → 2 |
| Word | 60 | 69 | 43 | 3 → 6 |

The cue-relative margin compares the cue's contribution with an absent-cue baseline. It is a **different estimand**, not corrected accuracy or demonstrated removal of a prior. Removing the cue also changes token positions and leaves an empty-message artifact in the existing template.

Completing absent scores for the two new candidate pairs would cost 192 scored continuations. It can extend this diagnostic, but it cannot change H by this subtraction or resolve the semantic validity of the candidates. That makes it optional rather than the main next experiment.

## 7. Competing explanations and the next discriminating evidence

| Explanation or hypothesis | Consistency with current evidence | What remains necessary |
| --- | --- | --- |
| A fixed status cue combines with a changing goal | Sufficient for the authored temperature/status examples and compatible with H | Independently validate the goal–cue relation; do not relabel it emoji sense change |
| Candidate-form effects shift absolute preferences | Observed coefficient and polarity changes support sensitivity | Separate length, morphology, specificity, and meaning in development; independent candidate validation |
| Ordinary lexical cues support the same computation | Words have positive mean H in every pair and higher means here | Comparable meaning/function and outcome-blind token/position controls |
| Emoji have a distinctive contextual advantage | Not established by current carrier comparison | A prespecified between-carrier contrast on validated, comparable materials |
| One shared attention route carries the output effect | Compatible but untested | Natural-state bidirectional interventions with calibration and positional controls on this endpoint |
| A context-dependent emoji sense changes | The current design does not require this | Same cue with independently validated distinct interpretations and discriminating outputs |

Word-versus-emoji input geometry differs on 84/96 inputs. Within words, cue a/b geometry differs on 12/48 context comparisons. A word can also repeat goal vocabulary or make the status more explicit. The larger word H therefore bounds an emoji-specific interpretation; it does not rank semantic understanding across carriers.

The affect-family contrast is interesting heterogeneity. Promoting the most favorable family directly to causal confirmation would import selection from these results. A follow-up may record the hypothesis, then test it on independently prepared materials with all planned comparators retained.

## 8. Connection to prior work

Zhang and Nanda show that activation-patching localization depends on corruption and evaluation choices. That motivates preserving the endpoint and calibration alongside each causal claim here; their experiments do not validate these emoji candidates. [Towards Best Practices of Activation Patching](https://arxiv.org/html/2309.16042v2), especially §§4–6.

Heimersheim and Nanda distinguish continuous changes from rank thresholds and discuss how a score difference can improve through either candidate. That supports reporting individual scores, margins, and both intervention directions. Our full-sequence contrast spans different teacher-forced trajectories; single-token logit arguments do not transfer unchanged. [How to use and interpret activation patching](https://arxiv.org/html/2404.15255v1), §§3–4.

Zhao et al. estimate answer biases with content-free inputs in few-shot tasks and examine contextual calibration. This is a useful comparison for baseline sensitivity, not evidence that the present table-wide offset is a pure prior or that absent subtraction yields calibrated accuracy. [Calibrate Before Use](https://proceedings.mlr.press/v139/zhao21c.html), §5.

EMODIS explicitly targets context-dependent emoji disambiguation. Its abstract helps delimit our present goal–cue compatibility task from a change in emoji sense. Only its abstract was inspected for this note; no dataset or full-method comparison is claimed. [Huang, Yu, and Yi, EMODIS](https://arxiv.org/abs/2511.07193).

These are focused connections, not a systematic novelty review. The paper contribution should be demonstrated by the design and evidence rather than a claim of being first.

## 9. Paper-ready integration proposal

Add a short **Exploratory extension: contextual output scoring** section after the existing results, with the full sensitivity and decomposition tables in the supplement. Preserve the original confirmatory lexical study as a distinct arm. The following draft can be edited into English prose:

> We examined whether ordinary output probabilities depend on the combination of a goal context and a cue. In 24 author-written development scenarios from six recurring families, we crossed two goal contexts with two cues and scored fixed continuation pairs using Llama 3.2 3B. The measurement uses complete teacher-forced sequence probabilities without a CLDR target, readout reset, or internal intervention. The same scenarios were evaluated with previously recorded word alternatives and two additional continuation pairs specified after the initial results.
>
> Mean emoji interaction was positive for all three tested continuation pairs (1.196–1.316 nats), and 19 of 24 scenarios retained positive interaction across all pairs. The polarity of the higher-scoring candidate changed across formulations on 52 of 96 emoji inputs. Word alternatives produced larger mean interactions in each formulation and polarity changes on 56 of 96 inputs. No scenario achieved author-aligned choices in all four conditions across all three formulations for either carrier. An exact four-score decomposition separates the interaction from offsets and main effects that also determine absolute preferences.
>
> A stable cue interpretation combined with a changing goal can produce this pattern. The earlier attention-path result concerns a different population and a readout-reset intervention; connecting that route to the output effect requires a separately specified natural-state test. The added measurements reuse the same development scenarios, and the candidate pairs jointly vary vocabulary, specificity, morphology, and token length. Their equivalence and the authored labels have not been independently assessed. A saved-score audit also found shared-prefix numerical residuals; removing their contribution did not change any interaction sign, and their computational source remains unresolved. We therefore report the observations as a descriptive measurement study.

The current Discussion and Conclusion in [main.tex](../paper/main.tex) still describe ordinary responses as future work. At integration, replace that statement with the precise status: **teacher-forced output scoring completed in development; free generation, independent confirmation, and output-linked causality remain untested**. Do not retrospectively turn the added study into a registered result. The manuscript and PDF are unchanged by this research-note revision.

## 10. Validation and provenance

Validation disposition: **Share with caveats**. The arithmetic and finite-inventory counts are reproducible; shared-prefix computational consistency is an open issue. Semantic validity, population generalization, and causality have not been established by these checks.

- Revalidate raw records, duplicate/missing identities, finite per-token scores and sums, complete runtime identity, source/specification hashes, and the recorded parity checks through the existing independent analyzer.
- Check all 144 reconstructions, H/4 identities, crossover equivalence, strict minimum margins, and original absent-subtraction invariants. Preserve every scenario and family.
- Keep generated receipts unchanged; the new analysis writes a separate output and refuses overwrite. Synthetic tests cover ties, orientation, invalid/missing/duplicate data, and cases where the stronger criteria fail despite positive H.
- All 16 new synthetic tests pass. The targeted regression [JUnit record](../validation/contextual_emoji_measurement_v0/tests.xml) records 152 test-case entries including subtests, with zero failures, errors, or skips. This validates code paths and arithmetic, not the unresolved model-level numerical issue.
- Keep compute validation separate: historical parity reproduced 384 scores exactly under the recorded runtime. The shared-CUDA trial observed about 16.49 seconds of simultaneous allocation with Aether; sustained co-execution and effects on Aether throughput were not evaluated. This is engineering context, not extra scientific evidence.
- Protected historical banks are not opened or reused. No publication, DOI creation, or remote workload change occurs here.

Key acquisition records:

| Record | SHA-256 |
| --- | --- |
| Original emoji raw cells | `ce090b817ea5c0ebf5382d1b1994a482f918d06043821d94157c0b2710980d97` |
| Original word raw cells | `1026d3001ad4390662bfec608cfeca28d1610f7ba7117b6401494d8fa929ad91` |
| Additional candidate raw cells | `ceeb391072ddfd42db7e464e5dbb715217dadeb90661516c6f1c2e326c872630` |
| Existing independent candidate analysis | `1512f4ad613a4d9d20473c1a33af326412299c3a7f3a0d031551716ca753c719` |

The new receipt includes the analysis-source digest and input provenance. Its SHA-256 is `806400d78608cc2999f9480d3b82b24a45fd4739f85f52d82a21f3f7cb4b39e8`. Run from the repository root, choosing an unused output path:

```sh
python3 scripts/analyze_contextual_emoji_measurement_v0.py \
  --run-dir validation/contextual_emoji_candidate_wording_v0/runtime_fix/shared_trial \
  --specification validation/contextual_emoji_candidate_wording_v0/runtime_fix/specification.json \
  --output /tmp/glyphprobe-measurement-check.json
```

The bilingual companion notebook executed all nine code cells top-to-bottom in a local Jupyter kernel and independently recalculates the prefix-length and decision-change diagnostics. Its generated SHA-256 is `20d713004666ffba83e97e529792dcc4a816e07e3b7e36be96763ebfb18d6d41`. The analysis cells use Python's standard library. To rebuild an executed notebook, install `nbformat==5.11.1`, `nbclient==0.11.0`, and `ipykernel==7.4.0` in a separate environment, then run the following with that environment's Python (use an unused output path):

```sh
python scripts/build_contextual_emoji_measurement_notebook_v0.py \
  --output /tmp/glyphprobe-measurement-check.ipynb
```

Kernel execution timestamps can change the notebook byte digest on a later run; the source/data pins and analytical results remain the reproducibility targets. The manuscript/PDF was not rebuilt; its preserved SHA-256 is `43a5931dd5d3de578818298c8a92fbc9f9244c08d0a821d30fce63e1f4645898`.

See the [original pilot](CONTEXTUAL_EMOJI_OUTPUT_PILOT_V0_RESULTS.md), [word control](CONTEXTUAL_EMOJI_WORD_CONTROL_V0_RESULTS.md), and [candidate sensitivity](CONTEXTUAL_EMOJI_CANDIDATE_WORDING_V0_RESULTS.md) reports for acquisition details. The [next-study plan](CONTEXTUAL_EMOJI_MEASUREMENT_NEXT_PLAN_V0.md) separates validated entry conditions, optional diagnostics, and still-open design choices.
