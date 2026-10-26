#!/usr/bin/env python3
"""Post-seal descriptive comparison; outputs human-derived data outside Git only."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path

from analyze_contextual_emoji_author_pilot_v0 import ROOT, canonical, private_directory, require, sha, write_new

MODEL_FILES = {
    'specification.json': '63e16fc7e60079032eade81a9cc599a1cea1b2db287373b077d08f078d162ecf',
    'independent_analysis.json': '8557d04e77b6c095022b3d97d5404024b1f7be8d1a101a93a6e54ebdcd4d2e35',
    'run1312/forwards.jsonl': '5bc84713d6305e0dff80898bb57d60d54d2c9ef01ab45b11f9158d59df8e5706',
}


def unique(rows, key):
    result = {row[key]: row for row in rows}
    require(len(result) == len(rows), 'Duplicate join key')
    return result


def metrics(rows):
    binary = [r for r in rows if r['human_choice'] in ('first', 'second')]
    comparable = [r for r in binary if r['model_choice'] != 'tie']
    return {'items': len(rows), 'human_categories': dict(Counter(r['human_choice'] for r in rows)),
            'human_binary': len(binary), 'human_nonbinary_or_missing': len(rows) - len(binary),
            'human_author_match_binary': sum(r['human_choice'] == r['authored_choice'] for r in binary),
            'human_author_differ_binary': sum(r['human_choice'] != r['authored_choice'] for r in binary),
            'human_model_comparable_binary': len(comparable),
            'human_model_match_binary': sum(r['human_choice'] == r['model_choice'] for r in comparable),
            'model_author_match_all': sum(r['model_choice'] == r['authored_choice'] for r in rows),
            'model_author_differ_all': sum(r['model_choice'] not in ('tie', r['authored_choice']) for r in rows),
            'model_ties_all': sum(r['model_choice'] == 'tie' for r in rows)}


def compare_rows(items, answers, assignments, cases, model_rows, forwards):
    item_ids = {r['id'] for r in items}
    answers, assignments = unique(answers, 'id'), unique(assignments, 'id')
    require(set(answers) == set(assignments) == item_ids and len(items) == len(item_ids), 'Key join coverage differs')
    cases, model_rows = unique(cases, 'input_id'), unique(model_rows, 'input_id')
    scored = {}
    for row in forwards:
        if row['phase'] != 'scientific':
            continue
        k = (row['input_id'], row['method'])
        require(k not in scored, 'Duplicate scientific score')
        require(row['status'] == 'completed', 'Incomplete score')
        require(math.isclose(math.fsum(row['candidate_token_logprobs']), row['sequence_logprob_sum'], rel_tol=0, abs_tol=1e-9), 'Token score sum differs')
        scored[k] = row['sequence_logprob_sum']
    joined = []
    for item in items:
        assignment, answer = assignments[item['id']], answers[item['id']]
        require(assignment['presentation_index'] == item['display_item'] - 1, 'Presentation index differs')
        identity = '/'.join(assignment[k] for k in ('pair_id', 'carrier', 'block_id', 'context', 'cue'))
        require(identity in cases and identity in model_rows, 'Selected model input missing')
        case, model = cases[identity], model_rows[identity]
        order = assignment['display_order']
        require(sorted(order) == ['a', 'b'], 'Invalid display order')
        require(all(case['candidates'][c]['prompt'] == item['prompt'] for c in ('a', 'b')), 'Prompt text differs')
        require([case['candidates'][c]['continuation'] for c in order] == item['responses'], 'Candidate text/order differs')
        require(case['candidates']['a']['family'] == assignment['family'] and case['candidates']['a']['eta'] == answer['authored_eta'], 'Metadata differs')
        require(answer['displayed_authored_response'] in (1, 2) and order[answer['displayed_authored_response'] - 1] == answer['original_authored_candidate'], 'Authored display mapping differs')
        a, b = (scored[(identity, method)] for method in ('padded_a', 'padded_b'))
        s = a - b
        require(s == model['new_s'], 'Saved analysis differs from raw selected scores')
        model_original = 'a' if s > 0 else ('b' if s < 0 else 'tie')
        require(model['new_choice'] == model_original, 'Model polarity differs')
        model_display = 'tie' if model_original == 'tie' else ('first' if order[0] == model_original else 'second')
        joined.append({'display_item': item['display_item'], 'source_input_id': identity,
                       **{k: assignment[k] for k in ('carrier', 'family', 'pair_id', 'block_id')},
                       'human_choice': (item['response'] or {}).get('choice', 'missing'),
                       'authored_choice': 'first' if answer['displayed_authored_response'] == 1 else 'second',
                       'model_choice': model_display, 'model_a_minus_b_nats': s,
                       'model_first_minus_second_nats': s if order[0] == 'a' else -s,
                       'semantic_accuracy': None})
    summary = {'stage': 'post_seal_descriptive_comparison', 'overall': metrics(joined),
               'by_carrier': {k: metrics([r for r in joined if r['carrier'] == k]) for k in sorted({r['carrier'] for r in joined})},
               'by_pair': {k: metrics([r for r in joined if r['pair_id'] == k]) for k in sorted({r['pair_id'] for r in joined})},
               'by_family': {k: metrics([r for r in joined if r['family'] == k]) for k in sorted({r['family'] for r in joined})},
               'claim_ceiling': 'not human-gold accuracy; binary subset is response-selected; single author; no significance tests',
               'model_forwards': 0, 'raw_response_recoding': False,
               'checks': {'unique_keys': True, 'selected_join_coverage': True, 'literal_prompt_candidate_equality': True,
                          'selected_raw_score_recalculation': True, 'display_order_mapping': True}}
    return summary, joined


def compare(output, package, handoff, write=False):
    output, package, handoff = map(Path, (output, package, handoff))
    seal = json.loads((output / 'phase_one_seal.json').read_text())
    require(all(sha(output / name) == digest for name, digest in seal['files'].items()), 'Pre-key interpretation changed')
    exposure = json.loads((output / 'comparison_exposure.json').read_text())
    require(exposure['phase_one_seal_sha256'] == sha(output / 'phase_one_seal.json'), 'Exposure not bound to sealed note')
    receipt = json.loads(handoff.read_text())
    require(sha(package / 'private/answer_key.json') == receipt['artifact_hashes']['authored_label_key'] and
            sha(package / 'private/assignment_key.json') == receipt['artifact_hashes']['assignment_key'], 'Private key hash differs')
    generator_path = ROOT / 'scripts/contextual_emoji_author_pilot_v0.py'
    require(sha(generator_path) == receipt['generator_sha256'], 'Generator identity differs')
    spec = importlib.util.spec_from_file_location('pilot_postseal_key_verification', generator_path)
    generator = importlib.util.module_from_spec(spec); spec.loader.exec_module(generator)
    generator.verify(package, root=ROOT)
    model_root = ROOT / 'validation/contextual_emoji_matched_shape_v1'
    require(all(sha(model_root / name) == digest for name, digest in MODEL_FILES.items()), 'Model provenance changed')
    model_analysis = json.loads((model_root / 'independent_analysis.json').read_text())
    require(model_analysis['status'] == 'verified_complete_matched_shape_grid' and model_analysis['numerical_gate_passed'], 'Model evidence gate not passed')
    summary, rows = compare_rows(
        json.loads((output / 'phase_one_items.json').read_text()),
        json.loads((package / 'private/answer_key.json').read_text())['items'],
        json.loads((package / 'private/assignment_key.json').read_text())['items'],
        json.loads((model_root / 'specification.json').read_text())['inputs'],
        model_analysis['analysis']['input_rows'],
        [json.loads(line) for line in (model_root / 'run1312/forwards.jsonl').read_text().splitlines()])
    summary['source_hashes'] = {**MODEL_FILES, 'phase_one_seal': sha(output / 'phase_one_seal.json'),
                                'exposure': sha(output / 'comparison_exposure.json'), 'comparison_code': sha(Path(__file__)),
                                'authored_label_key': sha(package / 'private/answer_key.json'), 'assignment_key': sha(package / 'private/assignment_key.json')}
    if write:
        private_directory(output)
        require(not any((output / n).exists() for n in ('comparison_summary.json', 'comparison_items.json')), 'Refusing existing comparison')
        write_new(output / 'comparison_summary.json', summary)
        write_new(output / 'comparison_items.json', rows)
    return summary, rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('output', 'package', 'handoff'):
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args()
    result, _ = compare(args.output, args.package, args.handoff, write=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
