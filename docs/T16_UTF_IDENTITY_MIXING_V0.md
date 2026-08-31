# T16 exact-UTF identity, mixing, and sequence length

T16-UTF isolates a simple side question: what changes when a sequence contains
the same exact emoji string repeatedly, distinct emoji strings from one Unicode
construction family, or emoji strings drawn across construction families?

## Exact sequence construction

The panel freezes four exact strings in each of six construction families:
single-scalar atomic glyphs, base-plus-VS16 presentation sequences, skin-tone
modifier sequences, three-scalar ZWJ sequences, regional-indicator flags, and
digit keycaps. Code points are stored explicitly and audited against each UTF-8
string.

For each family and one of four rotations, `clone_exact_utf` repeats one anchor
string byte-for-byte. `within_system_mix` cycles the four strings of that
family. `cross_system_mix` cycles through the six families using the same item
rotation. All use an empty separator, all start with the identical anchor, and
all three collapse to the same unique prompt at n=1. Sequence lengths are
1, 2, 4, 8, and 16, under four fixed wrappers.

## Capture and analysis

Gemma 2 2B IT and Mistral 7B Instruct v0.3 are used as frozen causal-language
model artifacts, but the prompts are raw wrapper strings rather than chat
instructions. Raw decoder-block output at the final common wrapper token is
captured at normalized depths 0.25, 0.5, 0.75, and 1.0.

The exact conditions generate 1,440 factorial records but only 1,248 unique
prompts per model because the three n=1 conditions share one prompt. The runner
captures each unique prompt once and maps the three records to that same array
row, making the n=1 equality an exact construction invariant.

For each model, depth, family, rotation, and wrapper, analysis reports:

- clone growth: cosine distance from the n=1 clone to the clone at n;
- within-family extra displacement: within-family mix versus matched clone;
- cross-family extra displacement: cross-family mix versus matched clone;
- cross-minus-within displacement.

Primary descriptive summaries average each endpoint over n=2, 4, 8, and 16,
with a 20,000-replicate bootstrap stratified by the six construction families.
All n-specific values and all exact token-count-matched pairs are retained.

## Claim boundary

Exact UTF identity does not imply matched tokenization after mixing. The
preflight records token counts, UTF-8 byte counts, scalar counts, and sequence
hashes for every record. Token-count-matched subsets are descriptive and cannot
rescue an unfavorable result. This study describes hidden-state geometry under
the observed tokenizer paths; it does not prove tokenizer-independent Unicode
composition, emoji meaning, or a causal circuit.

