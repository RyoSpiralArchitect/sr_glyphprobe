#!/usr/bin/env python3
"""Tokenizer-only census for prospective emoji-semantic controls.

This utility downloads the pinned Unicode emoji-test source, retains only
fully-qualified single-codepoint emoji, and records their exact tokenization
under a local Mistral tokenizer. It never loads model weights or performs a
model forward.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

from transformers import AutoTokenizer


LINE_RE = re.compile(
    r"^(?P<codepoints>[0-9A-F ]+)\s*;\s*(?P<status>[a-z-]+)\s*#\s*"
    r"(?P<glyph>\S+)\s+E[0-9.]+\s+(?P<name>.+)$"
)


def _load_existing_codepoints(repo_root: Path) -> set[str]:
    values: set[str] = set()
    for path in sorted((repo_root / "data" / "emoji_panels").glob("e1_*.yaml")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if "codepoint:" not in line:
                continue
            value = line.split("codepoint:", 1)[1].split("}", 1)[0].strip()
            values.add(value.removeprefix("U+").upper())
    return values


def _parse_source(text: str) -> tuple[str, list[dict[str, str]]]:
    group = ""
    subgroup = ""
    version = ""
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        if line.startswith("# Version:"):
            version = line.split(":", 1)[1].strip()
        elif line.startswith("# group:"):
            group = line.split(":", 1)[1].strip()
        elif line.startswith("# subgroup:"):
            subgroup = line.split(":", 1)[1].strip()
        else:
            match = LINE_RE.match(line)
            if match is None:
                continue
            row = match.groupdict()
            if row["status"] != "fully-qualified":
                continue
            codepoints = row["codepoints"].split()
            if len(codepoints) != 1:
                continue
            rows.append(
                {
                    "codepoint": codepoints[0],
                    "glyph": row["glyph"],
                    "name": row["name"],
                    "group": group,
                    "subgroup": subgroup,
                }
            )
    if not version or not rows:
        raise RuntimeError("Unicode emoji-test source did not parse")
    return version, rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--source-url",
        default="https://www.unicode.org/Public/17.0.0/emoji/emoji-test.txt",
    )
    args = parser.parse_args()

    with urllib.request.urlopen(args.source_url, timeout=30) as response:
        source = response.read()
    text = source.decode("utf-8")
    version, candidates = _parse_source(text)
    tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        local_files_only=True,
        trust_remote_code=False,
        use_fast=True,
    )
    existing = _load_existing_codepoints(Path(__file__).resolve().parents[1])

    by_subgroup: dict[str, list[dict[str, object]]] = defaultdict(list)
    rows: list[dict[str, object]] = []
    for item in candidates:
        ids = [int(value) for value in tokenizer.encode(item["glyph"], add_special_tokens=False)]
        name_ids = [
            int(value)
            for value in tokenizer.encode(item["name"], add_special_tokens=False)
        ]
        codepoint_literal = f"U+{item['codepoint']}"
        codepoint_ids = [
            int(value)
            for value in tokenizer.encode(codepoint_literal, add_special_tokens=False)
        ]
        decoded = tokenizer.decode(
            ids,
            clean_up_tokenization_spaces=False,
            skip_special_tokens=False,
        )
        row: dict[str, object] = {
            **item,
            "token_ids": ids,
            "token_count": len(ids),
            "name_token_ids": name_ids,
            "name_token_count": len(name_ids),
            "codepoint_literal": codepoint_literal,
            "codepoint_token_ids": codepoint_ids,
            "codepoint_token_count": len(codepoint_ids),
            "roundtrip_exact": decoded == item["glyph"],
            "used_in_e1": item["codepoint"] in existing,
        }
        rows.append(row)
        by_subgroup[str(item["subgroup"])].append(row)

    subgroup_summary = []
    for subgroup, items in sorted(by_subgroup.items()):
        unseen = [row for row in items if not row["used_in_e1"]]
        count_hist = Counter(int(row["token_count"]) for row in unseen)
        five = [row for row in unseen if row["token_count"] == 5]
        subgroup_summary.append(
            {
                "subgroup": subgroup,
                "group": items[0]["group"],
                "unseen_single_codepoint_count": len(unseen),
                "unseen_token_count_histogram": dict(sorted(count_hist.items())),
                "unseen_five_token_count": len(five),
                "five_token_unique_prefix3_count": len(
                    {tuple(row["token_ids"][:3]) for row in five}
                ),
                "five_token_unique_penultimate_count": len(
                    {int(row["token_ids"][-2]) for row in five}
                ),
                "five_token_unique_final_count": len(
                    {int(row["token_ids"][-1]) for row in five}
                ),
            }
        )

    payload = {
        "schema_version": 1,
        "status": "tokenizer_only_zero_forward_census",
        "source": {
            "url": args.source_url,
            "unicode_emoji_version": version,
            "sha256": hashlib.sha256(source).hexdigest(),
        },
        "model": {
            "canonical_id": "mistralai/Mistral-7B-v0.3",
            "revision": args.model.resolve().name,
            "tokenizer_class": type(tokenizer).__name__,
            "vocab_size": int(getattr(tokenizer, "vocab_size", len(tokenizer))),
        },
        "model_weights_loaded": False,
        "model_forward_calls": 0,
        "candidate_count": len(rows),
        "subgroups": subgroup_summary,
        "candidates": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
