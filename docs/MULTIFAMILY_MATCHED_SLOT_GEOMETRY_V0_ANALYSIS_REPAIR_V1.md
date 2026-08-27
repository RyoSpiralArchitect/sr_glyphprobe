# Matched-slot geometry v0 analysis repair v1

[日本語](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_ANALYSIS_REPAIR_V1.ja.md) · [Frozen v0 protocol](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0.md)

Repair ID: `glyphprobe-multifamily-matched-slot-geometry-v0-analysis-repair-v1`

## Why a repair is needed

The first joint-analysis attempt reached analysis-receipt serialization and
failed with `TypeError: Dict key must be str`. In the frozen YAML, the mapping
key written as `null` was parsed as Python `None`. The v0 statistic,
randomization, Holm correction, and outcome pattern had been computed in the
process, but no output directory was published and no analysis value was
printed or inspected.

The failure and the exact hashes of both already sealed run bundles are recorded
before this repair is executed.

## Authorized change

This repair changes one boundary only: before writing JSON, a `None` mapping key
is serialized as the string `"null"`. String keys and every leaf value are left
unchanged. The resulting analysis receipt records the repair ID and repair
manifest hash.

The repair does not change:

- either activation array or run receipt;
- the 5 × 10 panel or model roles;
- the five fixed depths;
- the sum-of-squares statistic;
- the synchronized within-family randomization algorithm;
- 19,999 draws, PCG64 seed `20260828`, or the p-value formula;
- the two-test Holm family or alpha;
- the outcome-pattern registry; or
- any report row or scientific claim boundary.

The wrapper imports and executes the frozen v0 analyzer. It verifies the public
repair manifest, the original freeze, and all four hashes in each run bundle
before analysis. This is a prospective serialization repair, not an
outcome-dependent analysis revision.

## Claim boundary

A passing repaired bundle establishes that the predeclared v0 analysis was
serialized and hash-sealed against the fixed inputs. It does not strengthen the
observational study into a semantic, causal, confirmatory, tokenizer-equivalent,
or Phase I paper-gate result.
