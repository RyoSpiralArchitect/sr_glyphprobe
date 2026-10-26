#!/usr/bin/env python3
"""Versioned development design; source-only assignment, never human gold."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "glyphprobe-contextual-two-track-development-v1"
SOURCE = "data/contextual_emoji_development_v0.jsonl"
SOURCE_SHA = "3222695420917983d79d84e55364dd07a86b61b29ecc4d6dfdadedccde72f394"
SEED = 2026101001
# block, property, local requested values, natural-language propositions about the cue,
# and propositions about the wider practical outcome. Affect deliberately changes construct.
DETAILS = [
 ("thermal_01", "drink temperature", "hot", "cold", "the drink is hot", "the drink is cold", "Mira has warmed up", "Mira has cooled down"),
 ("thermal_02", "soup temperature", "hot", "cold", "the soup is hot", "the soup is cold", "Leo has received the steaming soup he requested", "Leo has received the chilled soup he requested"),
 ("thermal_03", "room temperature", "warm", "cool", "the room is warm", "the room is cool", "Nora has warmed up in the room", "Nora has cooled down in the room"),
 ("thermal_04", "towel temperature", "warm", "cold", "the towel is warm", "the towel is cold", "Owen has received the warm towel he requested", "Owen has received the cold towel he requested"),
 ("sound_01", "device sound setting", "sound on", "muted", "the device is set to play sound", "the device is set to be silent", "the music is actually playing aloud", "the reading session is actually free of device sound"),
 ("sound_02", "phone alert setting", "sound on", "muted", "the phone is set for an audible call alert", "the phone is set for a silent call alert", "an incoming call has actually produced an audible alert", "an incoming call has actually produced no audible alert"),
 ("sound_03", "audio playback setting", "audio enabled", "audio muted", "audio playback is enabled", "audio playback is muted", "the visitors have actually heard the exhibit audio", "the visitors have actually viewed the exhibit without audio"),
 ("sound_04", "video sound setting", "unmuted", "muted", "the video sound is unmuted", "the video sound is muted", "the video has actually played audibly", "the video has actually played silently"),
 ("completion_01", "print-job status", "finished", "pending", "the print job is finished", "the print job is pending", "Ella has collected the finished print job", "Ella has changed the file before printing finished"),
 ("completion_02", "shipping status", "shipped", "awaiting shipment", "the parcel has shipped", "the parcel is awaiting shipment", "Finn's parcel has arrived at its destination", "Finn has changed the address before shipment"),
 ("completion_03", "report-export status", "complete", "pending", "the report export is complete", "the report export is pending", "Grace has sent the exported report", "Grace has cancelled the export before the file was finalized"),
 ("completion_04", "booking status", "confirmed", "awaiting confirmation", "the booking is confirmed", "the booking is awaiting confirmation", "Hugo's trip has gone ahead", "Hugo has revised the dates before confirmation"),
 ("affect_01", "visible facial expression", "smiling", "crying", "the expression conveys pleasure", "the expression conveys sadness", "the actor has successfully portrayed pleasure in the scene", "the actor has successfully portrayed sadness in the scene"),
 ("affect_02", "visible facial expression", "a smiling face", "a crying face", "the proposed face conveys cheerfulness", "the proposed face conveys sorrow", "the finished drawing conveys the requested cheerful mood", "the finished drawing conveys the requested sorrowful mood"),
 ("affect_03", "visible facial expression", "a smile", "tears", "the reaction conveys happiness", "the reaction conveys sadness", "the completed reunion scene conveys the requested happy reaction", "the completed farewell scene conveys the requested sad reaction"),
 ("affect_04", "visible facial expression", "smiling", "crying", "the face conveys contentment", "the face conveys distress", "the completed puppet shot conveys the requested contentment", "the completed puppet shot conveys the requested distress"),
 ("direction_01", "lift direction", "up", "down", "the lift is moving up", "the lift is moving down", "Maya has reached the sixth floor", "Maya has reached the second floor"),
 ("direction_02", "camera tilt direction", "upward", "downward", "the proposed camera tilt is upward", "the proposed camera tilt is downward", "the camera has reached the requested ceiling-facing position", "the camera has reached the requested floor-facing position"),
 ("direction_03", "shelf movement direction", "up", "down", "the proposed shelf movement is upward", "the proposed shelf movement is downward", "the shelf has been mounted at the requested higher position", "the shelf has been mounted at the requested lower position"),
 ("direction_04", "platform movement direction", "upward", "downward", "the planned platform motion is upward", "the planned platform motion is downward", "the platform has reached the requested raised position", "the platform has reached the requested lowered position"),
 ("weather_01", "forecast weather category", "sunny", "rainy", "the forecast is for sunshine", "the forecast is for rain", "Quinn's washing has dried outside", "Quinn's rain barrel has filled"),
 ("weather_02", "forecast weather category", "sunshine", "rainfall", "the forecast is for sunshine", "the forecast is for rainfall", "the outdoor scene has been filmed with the requested sunshine", "the outdoor scene has been filmed with the requested rainfall"),
 ("weather_03", "forecast weather category", "sunny", "rainy", "the forecast is for sunshine", "the forecast is for rain", "Sam has completed the solar-panel test in sunshine", "Sam has completed the rain-gauge test in rain"),
 ("weather_04", "forecast weather category", "sunny", "rainy", "the forecast is for sunshine", "the forecast is for rain", "Tess has finished painting the fence in dry weather", "Tess's garden has been watered sufficiently by rain"),
]

def require(ok, message):
    if not ok:
        raise ValueError(message)

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False)
        f.write("\n")

def sources(root=ROOT):
    require(sha(root / SOURCE) == SOURCE_SHA, "Development source changed")
    rows = [json.loads(x) for x in (root / SOURCE).read_text().splitlines()]
    require([r['block_id'] for r in rows] == [d[0] for d in DETAILS], "24-scenario order changed")
    require(len(set(r['family'] for r in rows)) == 6 and set(Counter(r['family'] for r in rows).values()) == {4}, "Family balance differs")
    return rows

def scene(row, detail, context, carrier, cue, arm):
    _, prop, p, q, ip, iq, sp, sq = detail
    target = p if context == 'p' else q
    token = '[no cue provided]' if carrier == 'absent' else (
        row['emoji_' + cue] if carrier == 'emoji' else row['planned_word_alternatives'][cue])
    natural = row['context_' + context].split('\n')[0].replace('{emoji}', token)
    if arm == 'bounded':
        return (f"The requested {prop} is: {target}.\n"
                f"Report of the {prop}: {token}\n"
                f"For this task, assume the report accurately describes the {prop}. "
                "It describes a state or category, not an instruction or a button action. "
                f"Judge only the requested {prop}; other goals and practical outcomes are outside this question. "
                "If the cue's meaning is unclear, the report's assumed accuracy does not resolve that meaning.")
    return natural

def questions(detail, context, arm, polarity='positive'):
    _, prop, p, q, ip, iq, sp, sq = detail
    interpretation, success = (ip, sp) if context == 'p' else (iq, sq)
    statements = {'local_match': f"the reported {prop} matches the requested {prop}"} if arm == 'bounded' else {
        'message_reading': f"the message suggests that {interpretation}",
        'outcome_evidence': f"the message alone establishes that {success}"}
    return [{'id': key, 'text': f"Is it {'true' if polarity == 'positive' else 'false'} that {value}?"}
            for key, value in statements.items()]

def inventory(root=ROOT):
    result = []
    for row, detail in zip(sources(root), DETAILS):
        for context in ('p', 'q'):
            for carrier in ('emoji', 'word', 'absent'):
                for cue in (('a', 'b') if carrier != 'absent' else ('none',)):
                    for arm in ('bounded', 'naturalistic'):
                        for polarity in ('positive', 'negative'):
                            prompt = scene(row, detail, context, carrier, cue, arm)
                            for question in questions(detail, context, arm, polarity):
                                result.append({'input_id': '::'.join((row['block_id'], context, carrier, cue, question['id'], polarity)),
                                    'block_id': row['block_id'], 'family': row['family'], 'context':context,
                                    'carrier':carrier, 'cue':cue, 'arm':arm, 'probe':question['id'], 'polarity':polarity,
                                    'stimulus':prompt, 'question':question['text'], 'author_reference':
                                    ((context == 'p') == (cue == 'a')) if carrier != 'absent' and arm == 'bounded' else None,
                                    'reference_status':'author_defined_not_human_gold',
                                    'prompt': prompt + '\nQuestion: ' + question['text'] + '\nAnswer:',
                                    'answers': {'a':' The answer is yes.', 'b':' The answer is no.'}})
            # Logical evidence anchors, separate from emoji interpretation and from carrier effects.
            success = detail[6] if context == 'p' else detail[7]
            for kind in ('complete_report', 'explicit_unknown'):
                anchor = (f"For this question, assume this report is accurate: {success}." if kind == 'complete_report' else
                          "The message explicitly says: I do not know whether the practical outcome happened.")
                for polarity in ('positive', 'negative'):
                    question = questions(detail, context, 'naturalistic', polarity)[1]
                    result.append({'input_id':'::'.join((row['block_id'], context, kind, 'outcome_evidence', polarity)),
                        'block_id':row['block_id'], 'family':row['family'], 'context':context,
                        'carrier':'anchor', 'cue':kind, 'arm':'evidence_anchor', 'probe':'outcome_evidence', 'polarity':polarity,
                        'stimulus':anchor, 'question':question['text'], 'author_reference':kind == 'complete_report',
                        'reference_status':'stipulated_logical_anchor_not_human_gold',
                        'prompt':anchor + '\nQuestion: ' + question['text'] + '\nAnswer:',
                        'answers':{'a':' The answer is yes.', 'b':' The answer is no.'}})
    require(len(result) == 1632 and len({r['input_id'] for r in result}) == 1632, 'Inventory count/identity changed')
    return result

def package(output, root=ROOT, seed=SEED):
    output = Path(output).resolve()
    require(not output.exists(), 'Package already exists')
    require(not output.is_relative_to(root), 'Keep author packets outside the repository')
    require(not any((p / '.git').exists() for p in (output, *output.parents)), 'No private packet in Git')
    rng = random.Random(seed)
    assignments = []
    rows = sources(root)
    for start in range(0, 24, 4):
        cells = [(arm, carrier) for arm in ('bounded','naturalistic') for carrier in ('emoji','word')]
        rng.shuffle(cells)
        views = [('p','a'), ('p','b'), ('q','a'), ('q','b')]
        rng.shuffle(views)
        for i, ((arm, carrier), (context, cue)) in enumerate(zip(cells, views)):
            row, detail = rows[start+i], DETAILS[start+i]
            assignments.append({'block_id':row['block_id'], 'family':row['family'], 'arm':arm,
                'carrier':carrier, 'context':context, 'cue':cue,
                'prompt':scene(row, detail, context, carrier, cue, arm), 'questions':questions(detail, context, arm)})
    rng.shuffle(assignments)
    packet_id = 'pkg_' + os.urandom(16).hex()
    items, key = [], []
    for a in assignments:
        item_id = 'item_' + os.urandom(16).hex()
        items.append({'id':item_id, 'prompt':a['prompt'], 'questions':a['questions']})
        key.append({'id':item_id, **{k:v for k,v in a.items() if k not in ('prompt','questions')}})
    packet = {'protocol_id':PROTOCOL, 'package_id':packet_id, 'language':'en', 'total_items':24, 'items':items}
    output.mkdir(parents=True, mode=0o700)
    for name in ('participant','private'):
        (output/name).mkdir(mode=0o700)
    write(output/'participant/participant.json', packet)
    write(output/'private/assignment.json', {'seed':seed, 'items':key, 'model_outcome_selection':False})
    manifest = {'protocol_id':PROTOCOL, 'package_id':packet_id, 'created_at_utc':datetime.now(timezone.utc).isoformat(),
        'generator_sha256':sha(Path(__file__)), 'source_sha256':SOURCE_SHA,
        'participant_sha256':sha(output/'participant/participant.json'), 'assignment_sha256':sha(output/'private/assignment.json'),
        'purpose':'post-disclosure author development pilot; not independent validation',
        'known_exposure':{'prior_model_results':True, 'prior_pilot_comparison':True},
        'allocation':{'items':24,'unique_scenarios':24,'bounded':12,'naturalistic':12,'emoji':12,'word':12,
            'one_each_arm_carrier_per_family':True,'primary_questions':36}}
    write(output/'manifest.json', manifest)
    for p in output.rglob('*.json'):
        p.chmod(0o600)
    return manifest

def verify_package(path, root=ROOT):
    path = Path(path).resolve()
    manifest = json.loads((path/'manifest.json').read_text())
    require(manifest['protocol_id'] == PROTOCOL and manifest['generator_sha256'] == sha(Path(__file__)), 'Package source differs')
    sources(root)
    for field, relative in [('participant_sha256','participant/participant.json'),('assignment_sha256','private/assignment.json')]:
        require(sha(path/relative) == manifest[field], 'Package content differs')
    packet = json.loads((path/'participant/participant.json').read_text())
    assignment = json.loads((path/'private/assignment.json').read_text())['items']
    require(len(packet['items']) == len(assignment) == 24, 'Package count differs')
    require(len({x['block_id'] for x in assignment}) == 24, 'Scenario repeats')
    source = {r['block_id']:(r,d) for r,d in zip(sources(root),DETAILS)}
    for item, a in zip(packet['items'], assignment):
        row, detail = source[a['block_id']]
        require(item['id'] == a['id'] and item['prompt'] == scene(row,detail,a['context'],a['carrier'],a['cue'],a['arm']) and
                item['questions'] == questions(detail,a['context'],a['arm']), 'Package stimulus differs')
    return packet, {'package_id':packet['package_id'], 'participant_sha256':manifest['participant_sha256'], 'manifest_sha256':sha(path/'manifest.json')}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('inventory','package'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'inventory':
        value = {'protocol_id':PROTOCOL, 'source_sha256':SOURCE_SHA, 'generator_sha256':sha(Path(__file__)),
            'inputs':inventory(), 'unique_scenarios':24, 'new_independent_scenarios':0, 'selection':'source_only_before_new_model_outputs'}
        write(args.output,value)
        print(json.dumps({'pairs':len(value['inputs']), 'sha256':sha(args.output)}))
    else:
        print(json.dumps(package(args.output), indent=2))

if __name__ == '__main__':
    main()
