# T17 glyph–name paper story v0

[日本語](PAPER_STORY_T17_GLYPH_NAME_V0.ja.md) · [T17 results](GLYPH_NAME_DEPTH_TRAJECTORY_V0_RESULTS.md) · [Current Phase I outline](PAPER_OUTLINE.md) · [T16 story](PAPER_STORY_T16_V0.md)

Status: **candidate submission spine, not a final manuscript claim freeze**.

## Working title

**From Raw Emoji Surface to Lexical Name: A Cross-Model Depth Atlas**

Alternatives:

1. **When Does an Emoji Become Its Name? Depth-Resolved Correspondence Across Language Models**
2. **Local Lexical Retrieval Without Global Manifold Alignment in Emoji Representations**
3. **Tracing Raw Emoji Surfaces to Unicode Names Across Decoder Depth**

The first title is the safest. “Become” is memorable but can overstate a
representational transformation, and “semantic” should not enter the title
before the new-population confirmation gate.

## One-sentence thesis

Across nine fixed language-model cells, a raw emoji surface becomes a more
reliable item-level key for its official Unicode name than for its codepoint
identifier by the middle-to-late network, but the onset and peak are
model-specific and the relation does not require global manifold alignment.

## Why this is a contribution

The paper should not lead with “emoji have meanings inside language models.”
That claim is too large for the evidence and obscures the cleaner object we
can measure. The contribution is a depth-resolved separation of three things
that are usually collapsed:

```text
raw Unicode surface        official lexical label        codepoint identifier
        🐈              ↔           CAT FACE          versus      U+1F408
             item retrieval can converge
                         without
            whole-manifold geometry converging
```

GlyphProbe contributes:

1. an auditable paired-view benchmark that holds item identity and context
   fixed while separating raw surface, official name, and codepoint literal;
2. a nine-model, nine-depth atlas with exact model revisions, endpoint labels,
   token-count-matched strata, and item-clustered uncertainty;
3. an empirical dissociation between local item retrieval and global CKA
   alignment; and
4. a negative structural result: there is no single shared late transition or
   monotone depth/size story on this roster.

This is useful even if the next confirmatory population weakens the aggregate
effect. It turns a vague question—“what does an emoji do internally?”—into a
testable distinction between lexical correspondence, identifier geometry,
tokenization, and global representation shape.

## Draft abstract

Emoji are compact human-readable symbols but enter language models as Unicode
strings processed by text tokenizers. This makes it unclear whether internal
similarities reflect lexical association, codepoint identity, tokenizer
structure, or a globally shared representational geometry. We construct an
auditable depth-resolved benchmark that pairs 292 raw emoji surfaces with
their official Unicode names and literal codepoint strings under two carriers
and four readout distances. Across nine exact model/tokenizer cells and nine
normalized depths, we collect 567,648 hidden-state readouts without generation
or intervention. The forward top-1 name-minus-codepoint retrieval contrast is
positive in all nine models from normalized depth 0.375 through the returned
final state; all nine item-bootstrap lower bounds are positive at depths 0.50,
0.75, 0.875, and 1.0, and token-count-matched point estimates are positive in
all nine models from 0.25 onward. The trajectory is not universal: two models
peak at the first block, one at 0.125, one at 0.75, and five at 0.875. At the
final state, item-pair margins favor names in all nine models, while centered
linear CKA favors names in only four. Thus raw emoji surfaces broadly acquire
item-specific lexical retrievability relative to codepoint identifiers, but
through heterogeneous depth paths and without consistent global manifold
alignment. The population was exposed in prior studies, so the atlas is
exploratory; it does not establish rendered-glyph perception, human-like
meaning, tokenizer independence, or causality.

## Evidence spine

| Study | What it fixed | Result | Role in the story |
|---|---|---|---|
| T9 | New 292-item reserve, one Mistral returned-final endpoint | Prospective item/name advantage over codepoint passed | Confirmatory single-cell anchor |
| T10 | Same population and contexts across nine exact model/tokenizer cells | Statistical signal across cells; registered practical cross-model rule failed | Honest mixed final-state boundary |
| T17-GN | Same final boundary plus nine normalized depths | Positive mid/late cross-section in 9/9, heterogeneous peaks, margin/CKA dissociation | Exploratory mechanism-shaping atlas |
| T16-UTF / X1 | Exact-string repetition, Unicode construction, length, and order controls | Tokenizer-conditional construction and order geometry | Confound boundary and appendix control, not the lexical result |

T17 must not retroactively rescue T10. T10 asked whether a frozen practical
cross-model rule held at one final endpoint; it did not. T17 asks why a shared
final threshold was brittle and finds that models reach the endpoint through
different trajectories.

## Main narrative

### 1. Introduction: one symbol, three identities

An emoji is simultaneously a visible human symbol, a Unicode string, and a
lexically named object. A model also sees a tokenizer-specific sequence. A
hidden-state similarity can therefore arise from several sources that deserve
separate controls. The paper asks the narrow question that can be answered:
when does the raw surface become a better item key for the official name than
for the codepoint identifier?

### 2. Benchmark: preserve identity, vary representation

Use the exact same item under three views and the same carrier-distance grid.
The codepoint literal is not a semantic null; it is an alternative symbolic
identifier for the same item. That makes name-minus-codepoint a relative
lexicalization contrast, not a meaning-versus-no-meaning contrast.

Make batch size one, endpoint semantics, exact model revisions, token-count
matching, and the 20,000 item bootstrap part of the scientific method rather
than implementation trivia.

### 3. Final-state anchor: positive signal, failed universal floor

Present T9 and T10 before the new atlas. T9 establishes that the measurement
can pass prospectively in one held-out Mistral cell. T10 shows that a positive
statistical component appears more broadly while the fixed practical
cross-model rule fails. This motivates depth as an explanatory variable
without selecting a favorable new endpoint.

### 4. Depth atlas: common destination, different routes

Lead with the nine trajectories, not a single aggregate. All nine point
estimates are positive from 0.375 onward, yet early states range from near zero
to very large positive values. Five models peak at 0.875, but three peak at or
before 0.125. “Late lexicalization” is therefore too simple. The accurate
description is heterogeneous onset with a shared positive mid/late
cross-section.

### 5. Metric dissociation: correspondence is not manifold conversion

Pairwise margins and top-1 retrieval ask whether each emoji stays closest to
its own name relative to alternatives. CKA asks whether the complete
between-item geometry aligns. Their 9/9 versus 4/9 split should be a main
result, not a footnote. It blocks the seductive story that the network simply
rotates a glyph manifold into a name manifold.

### 6. Unicode controls: boundary, not headline

T16-UTF and T16-UTF-X1 explain why the paper is careful. Exact repetition,
construction family, ordering, and token paths all alter hidden states. These
controls belong in a compact main-text limitation or the appendix. They show
that a raw Unicode surface is not a pure visual glyph and prevent the lexical
retrieval result from being renamed “visual semantics.”

### 7. Discussion: what the atlas enables next

The atlas yields a principled next experiment instead of a post-hoc favorite
layer. A new item population can first test whether the name advantage
survives aliases, paraphrases, multilingual labels, and matched tokenization.
Only after that confirmation should a common late window be selected for
causal removal, insertion, and restoration of name information.

## Figure and table spine

1. **Figure 1 — Three-view benchmark.** One raw emoji, its official name, and
   its codepoint literal under matched contexts; clearly label text-tokenizer
   input rather than raster vision.
2. **Figure 2 — Nine depth trajectories.** The committed T17 curve figure with
   a zero line and sampled-depth markers.
3. **Figure 3 — Local/global dissociation.** Per-model final top-1 or paired
   margin contrast beside final CKA contrast.
4. **Table 1 — Model and tokenizer roster.** Exact revisions, architecture,
   block count, matched-item count, and endpoint semantics.
5. **Table 2 — Onset, peak, and final values.** Use the compact T17 result
   table; move all carrier-by-distance cells to the appendix.

If space is tight, Figures 2 and 3 carry the paper. T16 sequence controls and
the full metric grid can remain in the appendix and repository evidence.

## Allowed and disallowed claims

| Claim | Status after T17 | Manuscript wording |
|---|---|---|
| Raw emoji surfaces retrieve their own official names better than codepoint literals at mid/late depth in these nine cells | supported descriptively on the exposed population | state with exact depths, roster, and uncertainty |
| The effect survives exact token-count matching | supported for point-estimate sign from depth 0.25 in 9/9 | token-count matched, not tokenizer independent |
| One shared late phase transition explains all models | contradicted by heterogeneous onset and peaks | report as a negative structural result |
| Item-specific retrieval implies global name-manifold alignment | not supported; final CKA contrast is positive in 4/9 | make the metric dissociation explicit |
| Larger Qwen models lexicalize emoji more strongly | not established | final values are ordered, trajectories are not; size is confounded |
| The model visually perceives or understands the glyph | unauthorized | raw Unicode text input only |
| T17 independently replicates T9/T10 | unauthorized | prior-exposed exploratory atlas |
| The relation is causal | unauthorized | reserve for a separately frozen intervention |

## The next confirmatory design

The most informative fresh population should be frozen as four label
families per raw emoji:

- official Unicode name;
- common alias or concise paraphrase;
- multilingual name with language fixed in advance;
- literal codepoint identifier.

Primary endpoint: official-name minus codepoint item retrieval at a
predeclared shared depth window, with raw emoji, carrier, distance,
token-count-matched stratum, model family, and multiplicity rule fixed before
opening. Secondary contrasts can distinguish Unicode-table memorization from
broader lexical association: official name versus alias, and English versus a
frozen non-English label. The causal experiment should remain downstream of
this gate.

## Submission decision

T17 supplies a cleaner representation-analysis paper than a broad “emoji
meaning” claim, but it is still exploratory. There are two defensible landing
points:

1. use T17 as the central atlas and label the new-population confirmation as
   the principal remaining gate; or
2. keep the existing T16 behavior/causality dissociation as the main paper and
   use T17 as a compact representation section that explains why lexical
   correspondence is not itself a causal meaning circuit.

The choice should be made by claim clarity and completed validation, not by
which trajectory looks largest. Until a fresh population is opened, option 2
has the stronger confirmatory spine; option 1 has the cleaner motivating
question.
