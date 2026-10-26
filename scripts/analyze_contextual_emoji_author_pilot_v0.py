#!/usr/bin/env python3
"""Local, key-free author-pilot description; never publish participant records.

The first stage accepts only a participant payload, final journal, and public
handoff hashes. It does not call the package generator or open either key.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat

ROOT = Path(__file__).resolve().parents[1]
CHOICES = ('first', 'second', 'both', 'neither', 'ambiguous', 'unclear', 'abstain')


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def private_directory(path):
    path = Path(path).absolute()
    require(not path.is_symlink(), 'Symlinked output refused')
    path = path.resolve()
    require(not path.is_relative_to(ROOT), 'Participant analysis must remain outside this repository')
    require(not any((p / '.git').exists() for p in (path, *path.parents)), 'Output is inside Git')
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    require(stat.S_IMODE(path.stat().st_mode) == 0o700, 'Output directory must have mode 700')
    return path


def write_new(path, value):
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode() + b'\n'
    with open(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def summarize(packet, records):
    state = records[-1]['state']
    require(state['locked'] and records[-1]['action'] == 'finalize', 'Finalized batch required')
    ids = [item['id'] for item in packet['items']]
    require(len(ids) == len(set(ids)) == packet['total_items'], 'Duplicate or missing participant items')
    require(set(state['responses']) <= set(ids), 'Orphan response')
    rows, choices, recognition = [], Counter(), Counter()
    naturalness = {field: Counter() for field in ('prompt', 'first', 'second')}
    for n, item in enumerate(packet['items'], 1):
        response = state['responses'].get(item['id'])
        history = [r for r in records[1:] if r['action'] == 'response' and r['body']['item_id'] == item['id']]
        choices[response['choice'] if response else 'missing'] += 1
        recognition[(response or {}).get('recognition') or 'missing'] += 1
        for field in naturalness:
            naturalness[field][(response or {}).get('naturalness', {}).get(field, 'missing')] += 1
        rows.append({'display_item': n, **item, 'response': response,
                     'save_count': len(history),
                     'saved_history': [{'at_utc': r['recorded_at_utc'], 'instruction_language': r['body']['instruction_language'],
                                        'response': r['body']['response']} for r in history]})
    completed = len(state['responses'])
    starts = [r for r in records[1:] if r['action'] == 'start']
    require(len(starts) == 1, 'Expected one batch-start event')
    final = records[-1]
    start_dt = datetime.fromisoformat(starts[0]['recorded_at_utc'])
    final_dt = datetime.fromisoformat(final['recorded_at_utc'])
    require(final_dt >= start_dt, 'Reversed batch timestamps')
    summary = {
        'stage': 'key_free_description', 'package_id': packet['package_id'],
        'denominators': {'planned': packet['total_items'], 'assigned': len(ids), 'completed_including_abstain': completed,
                         'eligible_non_abstain': completed - choices['abstain'], 'binary_choice_subset': choices['first'] + choices['second'],
                         'missing': len(ids) - completed},
        'choice_counts': {key: choices[key] for key in (*CHOICES, 'missing')},
        'recognition_counts': {key: recognition[key] for key in ('yes', 'no', 'unsure', 'missing')},
        'naturalness_counts': {field: {key: counts[key] for key in ('good', 'awkward', 'unclear', 'missing')} for field, counts in naturalness.items()},
        'nonempty_note_items': sum(bool((r['response'] or {}).get('note', '').strip()) for r in rows),
        'setup_self_report': state['setup'], 'known_participant_context': records[0]['participant_identity'],
        'journal_events': len(records) - 1, 'response_saves': sum(r['save_count'] for r in rows),
        'resaved_items': [r['display_item'] for r in rows if r['save_count'] > 1],
        'instruction_language_at_saved_actions': dict(Counter(r['body']['instruction_language'] for r in records[1:])),
        'batch_started_at_utc': starts[0]['recorded_at_utc'], 'batch_finalized_at_utc': final['recorded_at_utc'],
        'elapsed_wall_seconds_not_active_rating_time': (final_dt - start_dt).total_seconds(),
        'final_revision': state['revision'], 'finalized': True,
        'item_views_and_revisits': 'UNMEASURED', 'keys_or_model_scores_opened_by_this_stage': False,
        'independent_raters': 0, 'interpretation': 'descriptive author development pilot only; no recoding or exclusions'
    }
    require(sum(summary['choice_counts'].values()) == len(ids), 'Denominator mismatch')
    return summary, rows


def phase_one(package, journal, handoff, output=None):
    package, journal, handoff = map(Path, (package, journal, handoff))
    receipt = json.loads(handoff.read_text())
    participant_path = package / 'participant/participant.json'
    require(sha(participant_path) == receipt['artifact_hashes']['participant'], 'Participant hash changed')
    server_path = ROOT / 'scripts/serve_contextual_emoji_author_pilot_v0.py'
    require(sha(server_path) == receipt['interface_hashes']['server'], 'Pinned server changed')
    spec = importlib.util.spec_from_file_location('pilot_read_only_replay', server_path)
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)
    require(server.interface_identity(ROOT / 'web/author-pilot') == receipt['interface_hashes'], 'Interface/protocol changed')
    packet = server.parse_json(participant_path.read_bytes())
    server.validate_public_packet(packet)
    require(packet['package_id'] == receipt['package_id'], 'Package identity differs')
    raw = journal.read_bytes()
    require(raw.endswith(b'\n'), 'Partial journal; do not truncate')
    records = [server.parse_json(line) for line in raw.splitlines()]
    # Reuse the bound transition validator with an O_RDONLY descriptor. Do not
    # call Journal.__init__, acquire a writer lock, or open any package key.
    replay = server.Journal.__new__(server.Journal)
    replay.fd = os.open(journal, os.O_RDONLY)
    replay.binding = {'package_id': receipt['package_id'], 'manifest_sha256': receipt['manifest_sha256'],
                      'participant_sha256': receipt['artifact_hashes']['participant']}
    replay.interface_binding = receipt['interface_hashes']
    replay.items = {i['id'] for i in packet['items']}
    replay.state = {'revision': 0, 'locked': False, 'started': False, 'setup': None, 'responses': {}}
    replay.requests, replay.last_hash, replay.finalization = {}, '0' * 64, None
    try:
        replay._replay()
    finally:
        os.close(replay.fd)
    require(raw == journal.read_bytes(), 'Journal changed during analysis')
    summary, rows = summarize(packet, records)
    summary['source_hashes'] = {'journal': hashlib.sha256(raw).hexdigest(), 'participant': sha(participant_path),
                               'handoff': sha(handoff), 'analyzer': sha(Path(__file__))}
    summary['checks'] = {'journal_hash_chain': True, 'request_identity': True, 'state_transition_replay': True,
                         'package_and_interface_binding': True, 'no_orphan_responses': True, 'all_denominators_reconcile': True}
    if output is not None:
        output = private_directory(output)
        require(not any((output / n).exists() for n in ('phase_one_summary.json', 'phase_one_items.json')), 'Refusing to overwrite a phase-one analysis')
        write_new(output / 'phase_one_summary.json', summary)
        write_new(output / 'phase_one_items.json', rows)
    return summary, rows


def seal(output):
    output = private_directory(output)
    names = ('phase_one_summary.json', 'phase_one_items.json', 'PHASE_ONE.md', 'PHASE_ONE.ja.md')
    require(all((output / n).is_file() for n in names), 'Write both interpretation notes before opening keys')
    receipt = {'stage': 'pre_key_interpretation_seal', 'sealed_at_utc': datetime.now(timezone.utc).isoformat(),
               'files': {n: sha(output / n) for n in names}, 'keys_and_model_scores_opened': False,
               'claim_ceiling': 'analyst description before current key exposure; prior project knowledge remains'}
    write_new(output / 'phase_one_seal.json', receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('describe')
    for field in ('package', 'journal', 'handoff', 'output'):
        p.add_argument('--' + field, type=Path, required=True)
    p = sub.add_parser('seal'); p.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'seal':
        result = seal(args.output)
    else:
        result, _ = phase_one(args.package, args.journal, args.handoff, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
