# GlyphProbe: revision and public-release route

[日本語](POST_REVIEW_REVISION_20261007.ja.md) | [Experiment guide](../paper/EXPERIMENT_GUIDE.md) | [Next experiment option](CONTEXTUAL_EMOJI_CAUSAL_TRANSFER_PLAN_V0.md)

Status, 2026-10-07: the local working PDF is revised, and the first bounded
[contextual output pilot](CONTEXTUAL_EMOJI_OUTPUT_PILOT_V0_RESULTS.md) completed
288/288 scoring cells after the PDF was checked. The proposed causal study
remains incomplete. No external preregistration, DOI reservation, or public
deposit has occurred. A separate, same-scenario [192-cell word control](CONTEXTUAL_EMOJI_WORD_CONTROL_V0_RESULTS.md)
also completed: it is a development lexicalization comparison, with no new
causal intervention or human validation. The historical source baseline is commit
`8f4410de7012ae4b51b5fe4e65fcdeb92619f5b2`. The supplied submission-page text
records a later modification date; the exact uploaded PDF has not been compared
with this source baseline. Private review text is not included here.

## What to change

The current primary measurement is retrieval of CLDR keywords. A reader who
understands it as lexical correspondence has understood its operational target.
Clearer naming will reduce reading effort; broader claims require an endpoint
that measures a different behavior.

The revised question should be: **When does emoji information change a model's
response, and which internal messages carry that contribution?** This is a
research question, not an established result. Existing retrieval and intervention
results provide a starting point and reveal the limits of the present measurement.

Use descriptive experiment names throughout reader-facing explanations. Preserve
T19/T20/T21 identifiers in an appendix crosswalk, code, and historical records.
The paired experiment guide supplies the names, questions, populations, results,
and one running example. Consolidate terminology at the first example: raw emoji
text, official name, keyword, literal codepoint text, and readout position.

The manuscript revision should follow the scientific dependency:

1. What lexical relation can be read from hidden states?
2. What do fixed and optimized low-rank interventions establish?
3. What changes after a readout reset, and how does that differ from ordinary output?
4. Does a newly specified natural-context test connect emoji-origin information
   to the model's response?

The fourth step remains an incomplete study; the development output pilot is
not its causal or confirmatory result. The author's updated
decision is to revise the PDF, complete the new study, and only then publish.
Completion does not require a positive result: negative or uncalibratable
outcomes must remain visible. No public deposit or DOI reservation is authorized
by this planning document alone.

## Existing evidence that already answers a design concern

The 0.02 floor was a prespecified operational choice. The inspected records do
not justify interpreting it as a threshold for meaningful semantics. Explain
that limitation and report sensitivity without revising the historical test.

`scripts/summarize_revision_sensitivity_v0.py` reads five explicit compact result
files, binds them by SHA-256, and produces
`validation/post_review_revision_20261007/sensitivity_summary.json`. It uses no
model, tokenizer, protected target bank, randomization, or bootstrap. It holds
stored statistical tests fixed and examines observed-effect thresholds and
depth averages after the outcomes are known.

| Effect floor | Configurations meeting both observed-effect floors | Core configurations |
| --- | ---: | ---: |
| 0.02 | 9/9 | 4/4 |
| 0.03 | 9/9 | 4/4 |
| 0.04 | 8/9 | 4/4 |
| 0.06 | 6/9 | 4/4 |
| 0.08 | 4/9 | 3/4 |
| 0.09 | 2/9 | 1/4 |

The recorded partial-conjunction p-value remains 0.0027; no new p-value is
computed for a different threshold or depth. All three single late-depth
averages and all three leave-one-late-depth-out averages retain positive
point estimates exceeding 0.02 in both components for all nine models.
These are descriptive robustness results, not six new confirmations.

Neither low-rank intervention study acquires a positive site by reducing the
effect floor to zero: every stored site has a nonpositive lower bound for at
least one of necessity/sufficiency and a site IUT p-value above 0.05.
The optimized study's primary calibration failures remain unresolved; changing
the calibration threshold afterward would not establish a mechanism.

Blocks 21/24/27 are zero-based resolutions of inherited relative depths
0.75/0.875/1.0 in a 28-block model, using
`min(L - 1, floor(f * L))`. This explains their origin. It does not supply a
scientific argument that block 24 is the uniquely appropriate primary site.
The next study should select among a limited set of depth windows on development
data, then fix the choice before evaluating new scenario families.

## One additional experiment with a clear job

The [paired design option](CONTEXTUAL_EMOJI_CAUSAL_TRANSFER_PLAN_V0.md) proposes
a crossed context-by-emoji test with a normal language-model output score and
bidirectional intervention on messages from emoji positions. It replaces CLDR
labels as the new outcome source and does not reset the readout residual.

The progression is stimulus validity, ordinary behavioral contribution, then
causal intervention on the same score. A small development set checks feasibility;
new context/template families support a later confirmation. All 954 items in the
old CLDR assignment pool have already been allocated. New contexts do not turn
those emoji into untouched items, and the two retired target banks remain closed.

Contextual emoji disambiguation already has relevant prior work, including
[EMODIS](https://arxiv.org/abs/2511.07193). The candidate contribution is an
output-linked causal test, not the existence of contextual ambiguity. Interpretation
must also account for the metric and corruption dependence documented by
[Zhang and Nanda](https://arxiv.org/abs/2309.16042) and the intervention guidance
of [Heimersheim and Nanda](https://arxiv.org/abs/2404.15255).

## Public-release arrangement

**Default: a revised preprint and a reproducibility package on Zenodo.** Give the
paper and independently citable code/data package separate records and link
them. The paper should cite the exact package version used for its results.
Zenodo supports DOI reservation before publication and linked new versions;
reservation alone is not publication. See the official
[DOI guidance](https://help.zenodo.org/docs/deposit/describe-records/reserve-doi/)
and [versioning documentation](https://help.zenodo.org/docs/deposit/manage-versions/).

**Alternative without arXiv: paper on TechRxiv, artifacts on Zenodo.** IEEE's
[official overview](https://innovate.ieee.org/techrxiv/) describes a free
preprint service for computer science and related fields, with screening rather
than peer review. Its [DOI information](https://innovate.ieee.org/wp-content/uploads/2023/03/TechRxiv-Sell-Sheet-Final-4.13.2022-1.pdf)
describes DOI assignment. Current account/identifier requirements must be
checked before submission; the detailed FAQ could not be inspected here.

JST's [Jxiv](https://jxiv.jst.go.jp/jxiv_docs/ja/Jxiv_about_ja.html) also supports
English manuscripts and DOIs, but is not an interchangeable later mirror. Its
[June 2026 guidelines](https://jxiv.jst.go.jp/jxiv_docs/ja/Jxiv_guidelines_ja.html)
restrict manuscripts previously deposited elsewhere and simultaneous deposits;
they also impose conditions on versions revised after peer-review comments.
Those conditions need checking for this manuscript before choosing that route.

**Future alternative only: paper on arXiv, code/data on Zenodo.** The author
currently cannot submit to arXiv, so this is not the working release route.
arXiv also assigns a DOI;
first-time or new-category submissions may require endorsement and undergo
moderation. It is a distribution option, not a guarantee of acceptance or peer
review. See [DOIs](https://info.arxiv.org/help/doi.html),
[endorsement](https://info.arxiv.org/help/endorsement.html), and
[moderation](https://info.arxiv.org/help/moderation/index.html).

Decide the paper's primary deposit route before minting identifiers for the
same object. If a paper already has a DOI, follow Zenodo's existing-DOI guidance.
Do not reuse a paper DOI for a separate code/data package. Figshare is another
DOI-enabled repository, but adds no necessary capability to this plan.

Prepare the author-named preprint with accurate affiliation, funding and AI
disclosures, a non-conference preprint presentation, bibliography, version/date,
and a public reproducibility statement. Preserve the September submission and
its archive as historical versions. Audit actual redistribution rights for
included code/data; exclude model weights, local paths, and private reviewer
text. Carry a compact-only replay limitation if raw activations remain absent.

## Compute readiness observed in this session

The first `spiral status` check showed an idle RTX 5090 with no compute processes.
Subsequent preflight verified the complete existing 3B snapshot against the
historical artifact-manifest pin and found a working existing Torch environment.
The PDF-first output pilot then ran in an isolated checkout, with an immediate
availability check before each run. Its [result report](CONTEXTUAL_EMOJI_OUTPUT_PILOT_V0_RESULTS.md)
records the actual runtime, all raw scoring cells, and independent arithmetic
validation. The final occupancy check found no GPU compute process. This
establishes acquisition completion, not intervention correctness.

Use a new isolated checkout for the next experiment, verify availability again
immediately before GPU work, and save each completed shard. One pinned 3B
configuration is sufficient for development; a second family tests the selected
claim after its design is fixed. Larger models and a new large atlas can wait
until the endpoint is informative.

## Reproduce the descriptive summary

```bash
python3 scripts/summarize_revision_sensitivity_v0.py
```

The default prints the deterministic JSON without changing files. `--output`
accepts a new path and refuses to overwrite an existing report. Hash binding
documents the exact inputs; it does not supply missing scientific assumptions.
