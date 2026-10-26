#!/usr/bin/env python3
"""Prepare concealed author-pilot materials without reading any model outcomes.

The participant allowlist contains only neutral IDs and literal presentation
text. Original labels and deterministic assignment stay in separate private
files. This is author development work, never independent human validation.
CLI output deliberately excludes stimuli, keys, mappings, and random seeds.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import re
import secrets
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "glyphprobe-contextual-emoji-author-pilot-v0"
SELF_PATH = "scripts/contextual_emoji_author_pilot_v0.py"
SOURCE_PINS = {
    "development": {"path": "data/contextual_emoji_development_v0.jsonl", "sha256": "3222695420917983d79d84e55364dd07a86b61b29ecc4d6dfdadedccde72f394"},
    "candidate_wording": {"path": "data/contextual_emoji_candidate_wording_v0.json", "sha256": "480d236a87e40e20a4ea339e0514c2a06a0707ec248413ca0260e56868a52730"},
    "word_mapping_implementation": {"path": "scripts/contextual_emoji_word_control_v0.py", "sha256": "1589c0452e127b08d824604a139bab408e1dec87cff0a577d4578bb6d5aecfd4"},
    "candidate_mapping_implementation": {"path": "scripts/contextual_emoji_candidate_wording_v0.py", "sha256": "b7f856c45004c69ce57579e3365659baff7ee599130e8ae727cd68578a610455"},
}
ARTIFACTS = ("participant/participant.json", "private/answer_key.json", "private/assignment_key.json")
PROTECTED = {"p2_confirmatory_targets_v1.jsonl", "c1_causal_holdout_targets_v1.jsonl"}
PAIRS = ("original", "explicit_negation", "adjective_pair")
PARTICIPANT_FIELDS = {"protocol_id", "package_id", "language", "total_items", "items"}
ITEM_FIELDS = {"id", "prompt", "responses"}
PACKAGE_PATTERN = re.compile(r"pkg_[0-9a-f]{32}\Z")
ITEM_PATTERN = re.compile(r"item_[0-9a-f]{32}\Z")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe(path):
    path = Path(path)
    require(path.name not in PROTECTED and path.resolve().name not in PROTECTED, "Protected data access prohibited")
    return path


def sha256(path):
    return hashlib.sha256(safe(path).read_bytes()).hexdigest()


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def decode(value):
    def unique(pairs):
        result = {}
        for key, item in pairs:
            require(key not in result, "Duplicate JSON key")
            result[key] = item
        return result
    def invalid(value):
        raise ValueError("Nonfinite JSON constant")
    return json.loads(value, object_pairs_hook=unique, parse_constant=invalid)


def read_json(path):
    return decode(safe(path).read_text(encoding="utf-8"))


def write_exclusive(path, value):
    path = safe(path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb", closefd=False) as handle:
            handle.write(canonical(value))
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(fd)


def validate_participant(value):
    """Pure allowlist gate suitable for use by a participant-only local server."""
    require(type(value) is dict and set(value) == PARTICIPANT_FIELDS, "Participant top-level allowlist failed")
    require(value["protocol_id"] == PROTOCOL and type(value["package_id"]) is str and
        PACKAGE_PATTERN.fullmatch(value["package_id"]), "Participant protocol or opaque package ID invalid")
    require(value["language"] == "en" and type(value["total_items"]) is int and value["total_items"] == 24,
        "Participant language or denominator invalid")
    require(type(value["items"]) is list and len(value["items"]) == 24, "Exactly 24 participant items required")
    ids = []
    for item in value["items"]:
        require(type(item) is dict and set(item) == ITEM_FIELDS, "Participant item allowlist failed")
        require(type(item["id"]) is str and ITEM_PATTERN.fullmatch(item["id"]), "Participant item ID is not opaque")
        ids.append(item["id"])
        require(type(item["prompt"]) is str and 0 < len(item["prompt"]) <= 10000, "Invalid literal prompt")
        require(type(item["responses"]) is list and len(item["responses"]) == 2 and
            all(type(text) is str and 0 < len(text) <= 10000 for text in item["responses"]) and
            item["responses"][0] != item["responses"][1], "Invalid literal response pair")
        require("{emoji}" not in item["prompt"], "Unsubstituted presentation placeholder")
    require(len(set(ids)) == 24, "Duplicate participant item ID")


def validate_materials(blocks, panel):
    require(type(blocks) is list and len(blocks) == 24, "Exactly 24 source scenarios required")
    require(len({b["block_id"] for b in blocks}) == 24, "Duplicate source scenario")
    families = Counter(b["family"] for b in blocks)
    require(len(families) == 6 and set(families.values()) == {4}, "Six source families of four required")
    require(type(panel) is dict and panel["original_pair_id"] == "original" and
        [pair["pair_id"] for pair in panel["additional_pairs"]] == list(PAIRS[1:]), "Source response panel differs")
    for pair in panel["additional_pairs"]:
        require(all(type(pair[k]) is str and pair[k] for k in ("positive", "negative")) and
            pair["positive"] != pair["negative"], "Invalid additional literal responses")
    for block in blocks:
        require(type(block["eta"]) is int and block["eta"] in (-1, 1), "Invalid authored orientation")
        require(type(block["block_id"]) is str and type(block["family"]) is str, "Invalid source identity")
        require(set(block["planned_word_alternatives"]) == {"a", "b"}, "Source word alternatives differ")
        for key in ("emoji_a", "emoji_b", "candidate_a", "candidate_b"):
            require(type(block[key]) is str and block[key], "Missing literal source text")
        require(block["candidate_a"] != block["candidate_b"], "Source response alternatives coincide")
        for cue in ("a", "b"):
            require(type(block["planned_word_alternatives"][cue]) is str and block["planned_word_alternatives"][cue],
                "Missing literal source word")
        for context in ("p", "q"):
            require(type(block[f"context_{context}"]) is str and block[f"context_{context}"].count("{emoji}") == 1,
                "Source template must have one cue slot")
            for cue in ("a", "b"):
                expected = "a" if block["eta"] * (1 if (context, cue) in (("p", "a"), ("q", "b")) else -1) > 0 else "b"
                require(block["orientation"][f"context_{context}"][f"emoji_{cue}"] == expected,
                    "Source orientation and authored direction disagree")


def demo_materials():
    """Synthetic practice fixtures; never read development stimuli or outcomes."""
    blocks = []
    for index in range(24):
        block = {"block_id": f"synthetic_{index:02d}", "family": f"synthetic_family_{index // 4}",
            "eta": 1, "context_p": f"Synthetic practice scenario {index + 1}, goal P. Message: {{emoji}}",
            "context_q": f"Synthetic practice scenario {index + 1}, goal Q. Message: {{emoji}}",
            "emoji_a": "◇", "emoji_b": "□", "candidate_a": " Practice alternative one.",
            "candidate_b": " Practice alternative two.", "planned_word_alternatives": {"a": "diamond", "b": "square"},
            "orientation": {"context_p": {"emoji_a": "a", "emoji_b": "b"}, "context_q": {"emoji_a": "b", "emoji_b": "a"}}}
        blocks.append(block)
    panel = {"original_pair_id": "original", "additional_pairs": [
        {"pair_id": "explicit_negation", "positive": " Practice statement.", "negative": " Practice non-statement."},
        {"pair_id": "adjective_pair", "positive": " Practice possible alternative.", "negative": " Practice impossible alternative."}]}
    return blocks, panel


def load_sources(root, demo=False):
    root = Path(root).resolve()
    sources = {"generator": {"path": SELF_PATH, "sha256": sha256(Path(__file__))}}
    require(sha256(root / SELF_PATH) == sources["generator"]["sha256"], "Generator checkout differs")
    if demo:
        blocks, panel = demo_materials()
    else:
        for name, entry in SOURCE_PINS.items():
            require(sha256(root / entry["path"]) == entry["sha256"], "Pinned source changed")
            sources[name] = dict(entry)
        lines = (root / SOURCE_PINS["development"]["path"]).read_text(encoding="utf-8").splitlines()
        require(lines and all(line.strip() for line in lines), "Blank source record")
        blocks = [decode(line) for line in lines]
        panel = read_json(root / SOURCE_PINS["candidate_wording"]["path"])
    validate_materials(blocks, panel)
    return blocks, panel, sources


def response_candidates(block, panel, pair_id):
    if pair_id == "original":
        return {"a": block["candidate_a"], "b": block["candidate_b"]}
    pair = next(p for p in panel["additional_pairs"] if p["pair_id"] == pair_id)
    return {"a": pair["positive"] if block["eta"] == 1 else pair["negative"],
        "b": pair["negative"] if block["eta"] == 1 else pair["positive"]}


def opaque(seed, namespace, value):
    digest = hashlib.sha256(canonical([PROTOCOL, seed, namespace, value])).hexdigest()[:32]
    return ("pkg_" if namespace == "package" else "item_") + digest


def allocate(blocks, seed):
    """Latin balanced marginals; allocation never consults authored labels."""
    require(type(seed) is int and 0 <= seed < 2**256, "Private seed must be a 256-bit nonnegative integer")
    rng = random.Random(seed)
    families = sorted({b["family"] for b in blocks})
    rng.shuffle(families)
    pair_order = list(PAIRS)
    rng.shuffle(pair_order)
    assignments = []
    for family_index, family in enumerate(families):
        ids = sorted(b["block_id"] for b in blocks if b["family"] == family)
        rng.shuffle(ids)
        conditions = [("p", "a"), ("p", "b"), ("q", "a"), ("q", "b")]
        rng.shuffle(conditions)
        carriers = ["emoji", "emoji", "word", "word"]
        rng.shuffle(carriers)
        orders = [["a", "b"], ["a", "b"], ["b", "a"], ["b", "a"]]
        rng.shuffle(orders)
        pair_for_carrier = {}
        for carrier in ("emoji", "word"):
            pair_for_carrier[carrier] = [pair_order[family_index % 3], pair_order[(family_index + 1) % 3]]
            rng.shuffle(pair_for_carrier[carrier])
        for block_id, (context, cue), carrier, order in zip(ids, conditions, carriers, orders):
            assignments.append({"block_id": block_id, "family": family, "carrier": carrier,
                "pair_id": pair_for_carrier[carrier].pop(), "context": context, "cue": cue, "display_order": order})
    rng.shuffle(assignments)
    return assignments


def balance_counts(assignments):
    require(type(assignments) is list and len(assignments) == 24, "Exactly 24 assignments required")
    require(len({r["block_id"] for r in assignments}) == 24, "Scenario repeated or omitted")
    grouped = defaultdict(list)
    for row in assignments:
        require(row["carrier"] in ("emoji", "word") and row["pair_id"] in PAIRS and
            (row["context"], row["cue"]) in (("p", "a"), ("p", "b"), ("q", "a"), ("q", "b")) and
            row["display_order"] in (["a", "b"], ["b", "a"]), "Invalid assignment condition")
        grouped[row["family"]].append(row)
    require(len(grouped) == 6 and {len(v) for v in grouped.values()} == {4}, "Family allocation differs")
    for group in grouped.values():
        require(Counter((r["context"], r["cue"]) for r in group) == Counter({(c, v): 1 for c in ("p", "q") for v in ("a", "b")}),
            "Family context/cue coverage differs")
        require(Counter(r["carrier"] for r in group) == {"emoji": 2, "word": 2}, "Family carrier balance differs")
        require(Counter(r["display_order"][0] for r in group) == {"a": 2, "b": 2}, "Family response-order balance differs")
    require(Counter(r["pair_id"] for r in assignments) == {p: 8 for p in PAIRS}, "Candidate pair balance differs")
    require(Counter((r["carrier"], r["pair_id"]) for r in assignments) == {(c, p): 4 for c in ("emoji", "word") for p in PAIRS},
        "Carrier/pair balance differs")
    return {"items": 24, "unique_scenarios": 24, "families": 6, "items_per_family": 4,
        "context_cue_combinations_per_family": 4, "carrier_totals": {"emoji": 12, "word": 12},
        "items_per_carrier_per_family": 2, "candidate_pairs": 3, "items_per_candidate_pair": 8,
        "items_per_carrier_candidate_pair": 4, "original_a_first": 12, "original_b_first": 12,
        "original_a_first_per_family": 2, "original_b_first_per_family": 2, "absent_items": 0,
        "repeated_scenarios": 0, "independent_raters": 0, "planned_author_raters": 1}


def objects(blocks, panel, sources, seed, demo=False):
    validate_materials(blocks, panel)
    assignments = allocate(blocks, seed)
    counts = balance_counts(assignments)
    package_id = opaque(seed, "package", {"sources": sources, "demo": demo})
    by_block = {b["block_id"]: b for b in blocks}
    items, answers, allocation = [], [], []
    for position, assignment in enumerate(assignments):
        block = by_block[assignment["block_id"]]
        item_id = opaque(seed, "item", [package_id, assignment["block_id"]])
        context, cue = assignment["context"], assignment["cue"]
        surface = block[f"emoji_{cue}"] if assignment["carrier"] == "emoji" else block["planned_word_alternatives"][cue]
        candidates = response_candidates(block, panel, assignment["pair_id"])
        items.append({"id": item_id, "prompt": block[f"context_{context}"].replace("{emoji}", surface),
            "responses": [candidates[c] for c in assignment["display_order"]]})
        author_candidate = block["orientation"][f"context_{context}"][f"emoji_{cue}"]
        answers.append({"id": item_id, "original_authored_candidate": author_candidate,
            "displayed_authored_response": assignment["display_order"].index(author_candidate) + 1,
            "authored_eta": block["eta"], "label_status": "author_defined_not_human_validated"})
        allocation.append({"id": item_id, "presentation_index": position, **assignment})
    participant = {"protocol_id": PROTOCOL, "package_id": package_id, "language": "en", "total_items": 24, "items": items}
    validate_participant(participant)
    answer_key = {"protocol_id": PROTOCOL, "package_id": package_id,
        "status": "original_authored_orientation_preserved_not_human_ground_truth", "items": answers}
    assignment_key = {"protocol_id": PROTOCOL, "package_id": package_id, "seed": seed,
        "algorithm": "six_family_balanced_latin_marginals_v0", "selection_uses_model_outcomes": False,
        "sources": sources, "items": allocation}
    return participant, answer_key, assignment_key, counts


def secure_entry(path, directory=False):
    require(not path.is_symlink(), "Package symlink prohibited")
    info = path.stat()
    require((stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)), "Package entry type invalid")
    require(stat.S_IMODE(info.st_mode) == (0o700 if directory else 0o600), "Package permissions are not owner-only")
    require(info.st_uid == os.getuid(), "Package is not owned by the current user")


def build(root, output, seed=None, demo=False):
    output = Path(output)
    require(output.is_absolute(), "Output must be an absolute path")
    require(not output.exists() and not output.is_symlink(), "Refusing existing package output")
    blocks, panel, sources = load_sources(root, demo=demo)
    seed = secrets.randbits(256) if seed is None else seed
    participant, answer, assignment, counts = objects(blocks, panel, sources, seed, demo)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir(mode=0o700, exist_ok=False)
    output.chmod(0o700)
    for name in ("participant", "private"):
        (output / name).mkdir(mode=0o700)
        (output / name).chmod(0o700)
    for relative, value in zip(ARTIFACTS, (participant, answer, assignment)):
        write_exclusive(output / relative, value)
    manifest = {"protocol_id": PROTOCOL, "schema_version": 1, "package_id": participant["package_id"],
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "synthetic_demo" if demo else "author_development_pilot",
        "claim_ceiling": "one previously involved author; concealed scores and labels; not independent human validation",
        "sources": sources, "counts": counts,
        "artifacts": {name: sha256(output / name) for name in ARTIFACTS}}
    write_exclusive(output / "manifest.json", manifest)
    return verify(output, root=root)


def verify(package, root=ROOT):
    """Strict full-package check; return only nonstimulus aggregate metadata."""
    package = Path(package)
    require(package.is_absolute(), "Package must be an absolute path")
    for relative in (".", "participant", "private"):
        secure_entry(package / relative, directory=True)
    require({p.name for p in (package / "participant").iterdir()} == {"participant.json"}, "Participant directory contains extra files")
    require({p.name for p in (package / "private").iterdir()} == {"answer_key.json", "assignment_key.json"}, "Private directory contains extra files")
    require({p.name for p in package.iterdir()} == {"participant", "private", "manifest.json"}, "Package root contains extra files")
    for relative in (*ARTIFACTS, "manifest.json"):
        secure_entry(package / relative)
    manifest = read_json(package / "manifest.json")
    require(type(manifest) is dict and set(manifest) == {"protocol_id", "schema_version", "package_id", "created_at_utc",
        "mode", "claim_ceiling", "sources", "counts", "artifacts"}, "Manifest allowlist failed")
    require(manifest["protocol_id"] == PROTOCOL and manifest["schema_version"] == 1 and
        manifest["mode"] in ("synthetic_demo", "author_development_pilot") and
        type(manifest["created_at_utc"]) is str, "Manifest identity invalid")
    require(set(manifest["artifacts"]) == set(ARTIFACTS), "Manifest artifact inventory invalid")
    for relative, expected in manifest["artifacts"].items():
        require(type(expected) is str and re.fullmatch(r"[0-9a-f]{64}", expected) and sha256(package / relative) == expected,
            "Package artifact hash mismatch")
    participant, answer, assignment = [read_json(package / relative) for relative in ARTIFACTS]
    validate_participant(participant)
    require(type(assignment) is dict and type(assignment.get("seed")) is int, "Private assignment seed missing")
    demo = manifest["mode"] == "synthetic_demo"
    blocks, panel, sources = load_sources(root, demo=demo)
    require(sources == manifest["sources"], "Manifest source binding mismatch")
    expected_participant, expected_answer, expected_assignment, counts = objects(blocks, panel, sources, assignment["seed"], demo)
    require(participant == expected_participant, "Participant material differs from source-bound assignment")
    require(answer == expected_answer, "Original authored key differs")
    require(assignment == expected_assignment, "Private assignment differs")
    require(manifest["package_id"] == participant["package_id"] and manifest["counts"] == counts, "Manifest summary differs")
    require(manifest["claim_ceiling"] == "one previously involved author; concealed scores and labels; not independent human validation",
        "Claim ceiling changed")
    return {"status": "verified", "protocol_id": PROTOCOL, "package_id": participant["package_id"],
        "mode": manifest["mode"], "total_items": 24, "participant_sha256": manifest["artifacts"][ARTIFACTS[0]],
        "manifest_sha256": sha256(package / "manifest.json"),
        "source_hashes": {name: entry["sha256"] for name, entry in sources.items()},
        "counts": counts, "checks": {"participant_allowlist": True, "source_literal_replay": True,
            "private_assignment_replay": True, "original_authored_labels_preserved": True,
            "allocation_balanced": True, "all_artifact_hashes": True, "owner_only_permissions": True,
            "model_outcomes_read": False, "protected_banks_read": False, "tokenizer_calls": 0,
            "model_forwards": 0, "human_judgments_collected": 0}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("build")
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seed", help="Optional private reproducibility seed; omitted means random 256-bit seed")
    p.add_argument("--demo", action="store_true", help="Synthetic material only; no real stimulus source is read")
    p = sub.add_parser("inspect")
    p.add_argument("--package", type=Path, required=True)
    p.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        if args.command == "build":
            seed = int(args.seed) if args.seed is not None else None
            result = build(args.root, args.output, seed=seed, demo=args.demo)
        else:
            result = verify(args.package, args.root)
    except Exception:
        # Do not echo untrusted object values, private seeds, keys or stimuli.
        print(json.dumps({"status": "refused", "reason": "Package construction or verification failed; no concealed content emitted."}))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
