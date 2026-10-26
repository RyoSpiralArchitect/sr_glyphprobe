#!/usr/bin/env python3
"""Read-only, assignment-free description of the finalized v1 author pilot.

Human-linked outputs must stay outside Git. No assignment or model-result file
is opened here, including during replay. Undecidable answers remain null.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import importlib.util
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


server = load('two_track_analysis_server', ROOT / 'scripts/serve_contextual_emoji_two_track_v1.py')
helpers = load('two_track_private_helpers', ROOT / 'scripts/analyze_contextual_emoji_author_pilot_v0.py')
require, sha, write_new = helpers.require, helpers.sha, helpers.write_new
PROBES = ('local_match', 'message_reading', 'outcome_evidence')
STATUSES = ('yes', 'no', 'undecidable', 'abstain', 'missing')


def answer_status(response, probe):
    if response is None:
        return 'missing'
    if response['abstain']:
        return 'abstain'
    judgment = response['judgments'][probe]
    if not judgment['decidable']:
        return 'undecidable'
    return 'yes' if judgment['answer'] else 'no'


def summarize(packet, records):
    server.validate_packet(packet)
    require(len(records) > 1, 'No finalized responses')
    state, final = records[-1]['state'], records[-1]
    require(state['locked'] and final['action'] == 'finalize', 'Explicitly finalized batch required')
    ids = {item['id'] for item in packet['items']}
    require(set(state['responses']) <= ids, 'Orphan response')
    rows = []
    by_probe = {probe: Counter() for probe in PROBES}
    clarity, recognition, reasons = Counter(), Counter(), Counter()
    starts = [r for r in records[1:] if r['action'] == 'start']
    require(len(starts) == 1, 'Expected one start event')
    for number, item in enumerate(packet['items'], 1):
        response = state['responses'].get(item['id'])
        if response is not None:
            server.Journal._response({k:v for k,v in response.items() if k != 'saved_at_utc'})
            expected = set() if response['abstain'] else {q['id'] for q in item['questions']}
            require(set(response['judgments']) == expected, 'Unexpected or missing judgment')
        history = [r for r in records[1:] if r['action'] == 'response' and r['body']['item_id'] == item['id']]
        statuses = {q['id']: answer_status(response, q['id']) for q in item['questions']}
        for probe, status in statuses.items():
            by_probe[probe][status] += 1
        clear = (response or {}).get('language_clear')
        clarity['missing' if clear is None else 'yes' if clear else 'no'] += 1
        recognition[(response or {}).get('recognition') or 'missing'] += 1
        reasons.update((response or {}).get('reasons', []))
        rows.append({'display_item': number, **item, 'response': response, 'statuses': statuses,
                     'save_count': len(history), 'saved_history': [
                         {'at_utc': r['recorded_at_utc'], 'instruction_language': r['body']['instruction_language'],
                          'response': r['body']['response']} for r in history]})
    times = [datetime.fromisoformat(r['recorded_at_utc']) for r in records[1:]]
    require(all(t.tzinfo is not None for t in times), 'Timestamp lacks timezone')
    require(times == sorted(times), 'Reversed event timestamps')
    question_counts = {p: {s: by_probe[p][s] for s in STATUSES} for p in PROBES}
    totals = Counter()
    for counts in question_counts.values():
        totals.update(counts)
    require(sum(totals.values()) == sum(len(i['questions']) for i in packet['items']), 'Question denominator differs')
    natural_joint = Counter((r['statuses']['message_reading'], r['statuses']['outcome_evidence'])
                            for r in rows if 'message_reading' in r['statuses'])
    summary = {
        'stage': 'assignment_free_human_description', 'package_id': packet['package_id'],
        'scene_denominators': {'planned': len(ids), 'saved_including_abstain': len(state['responses']),
                               'abstain': sum(r['abstain'] for r in state['responses'].values()),
                               'missing': len(ids) - len(state['responses'])},
        'judgment_denominators': {'planned': sum(totals.values()), 'decidable': totals['yes'] + totals['no'],
                                  'undecidable': totals['undecidable'], 'abstain': totals['abstain'], 'missing': totals['missing']},
        'by_probe': question_counts,
        'naturalistic_joint_counts': [{'message_reading': a, 'outcome_evidence': b, 'scenes': count}
                                     for (a,b),count in sorted(natural_joint.items())],
        'language_clear_counts': {k: clarity[k] for k in ('yes','no','missing')},
        'recognition_counts': {k: recognition[k] for k in ('yes','no','unsure','missing')},
        'reason_item_counts_multiple_allowed': {k: reasons[k] for k in sorted(server.REASONS)},
        'items_without_reason_selection': sum(not (r['response'] or {}).get('reasons') for r in rows),
        'nonempty_note_items': sum(bool((r['response'] or {}).get('note','').strip()) for r in rows),
        'setup_self_report': state['setup'], 'known_participant_context': records[0]['participant_identity'],
        'response_saves': sum(r['save_count'] for r in rows),
        'resaved_items': [r['display_item'] for r in rows if r['save_count'] > 1],
        'journal_mutations': len(records)-1, 'final_revision': state['revision'],
        'instruction_language_at_saved_actions': dict(Counter(r['body']['instruction_language'] for r in records[1:])),
        'batch_started_at_utc': starts[0]['recorded_at_utc'], 'batch_finalized_at_utc': final['recorded_at_utc'],
        'elapsed_wall_seconds_not_active_rating_time': (times[-1] - datetime.fromisoformat(starts[0]['recorded_at_utc'])).total_seconds(),
        'item_views_and_revisits': 'UNMEASURED', 'finalized': True,
        'assignment_or_model_scores_opened_by_this_stage': False, 'independent_raters': 0,
        'claim_ceiling': 'one previously exposed author; instrument development only; no imputation or exclusions'
    }
    return summary, rows


def phase_one(package, journal, output=None):
    package, journal = Path(package), Path(journal)
    participant_path, manifest_path = package/'participant/participant.json', package/'manifest.json'
    for p in (participant_path, manifest_path, journal):
        require(p.is_file() and not p.is_symlink(), 'Missing or linked input')
    manifest = server.base.parse_json(manifest_path.read_bytes())
    require(manifest['protocol_id'] == server.design.PROTOCOL, 'Manifest protocol differs')
    require(manifest['generator_sha256'] == sha(ROOT/'scripts/contextual_emoji_two_track_v1.py'), 'Generator changed')
    require(manifest['source_sha256'] == server.design.SOURCE_SHA, 'Development-source identity differs')
    require(sha(participant_path) == manifest['participant_sha256'], 'Participant hash differs')
    packet = server.base.parse_json(participant_path.read_bytes())
    server.validate_packet(packet)
    require(packet['package_id'] == manifest['package_id'], 'Package identity differs')
    raw = journal.read_bytes()
    require(raw and raw.endswith(b'\n'), 'Empty/partial journal; do not truncate')
    records = [server.base.parse_json(line) for line in raw.splitlines()]
    # Deliberately bypass __init__: no writer lock, append descriptor, key read,
    # header creation, journal repair, or participant action is allowed here.
    replay = server.Journal.__new__(server.Journal)
    replay.fd = os.open(journal, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    replay.packet = packet
    replay.binding = {'package_id': manifest['package_id'], 'manifest_sha256': sha(manifest_path),
                      'participant_sha256': manifest['participant_sha256']}
    replay.interface_binding = server.interface_identity()
    replay.items = {i['id'] for i in packet['items']}
    replay.state = {'revision':0, 'locked':False, 'started':False, 'setup':None, 'responses':{}}
    replay.requests, replay.last_hash, replay.finalization = {}, '0'*64, None
    try:
        replay._replay()
    finally:
        os.close(replay.fd)
    require(raw == journal.read_bytes(), 'Journal changed during analysis')
    summary, rows = summarize(packet, records)
    require(len(rows) == manifest['allocation']['items'] and
            summary['judgment_denominators']['planned'] == manifest['allocation']['primary_questions'], 'Allocation counts differ')
    summary['source_hashes'] = {'journal': hashlib.sha256(raw).hexdigest(), 'participant': sha(participant_path),
                              'manifest': sha(manifest_path), 'analyzer': sha(__file__), 'helpers': sha(helpers.__file__)}
    summary['checks'] = {'read_only_hash_chain_and_state_replay': True, 'package_and_interface_binding': True,
                         'monotonic_timestamps': True, 'all_denominators_reconcile': True}
    if output is not None:
        output = helpers.private_directory(output)
        require(not any((output/n).exists() for n in ('phase_one_summary.json','phase_one_items.json')), 'Existing analysis preserved')
        write_new(output/'phase_one_summary.json', summary)
        write_new(output/'phase_one_items.json', rows)
    return summary, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('describe')
    for name in ('package','journal','output'):
        p.add_argument('--'+name, type=Path, required=True)
    p = sub.add_parser('seal'); p.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'seal':
        result = helpers.seal(args.output)
    else:
        result, _ = phase_one(args.package, args.journal, args.output)
    print(helpers.json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
