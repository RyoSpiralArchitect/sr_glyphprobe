#!/usr/bin/env python3
"""Offline, guarded two-track development acquisition; never author data."""
from __future__ import annotations
import argparse
from collections import Counter
import gc
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import time

ROOT = Path(__file__).resolve().parents[1]
OLD_SPEC = 'validation/contextual_emoji_matched_shape_v1/specification.json'
OLD_SHA = '63e16fc7e60079032eade81a9cc599a1cea1b2db287373b077d08f078d162ecf'
PREFIX = 'scripts/contextual_emoji_prefix_consistency_v0.py'
PREFIX_SHA = '5ee9d2120c51e26db936ef37e0e1d4607aaf606fad41fb4970fc20210b985d65'
MAX_FORWARDS = 3296
WALL_SECONDS = 1800

def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

design = module(ROOT/'scripts/contextual_emoji_two_track_v1.py', 'two_track_design')
design.require(design.sha(ROOT/PREFIX) == PREFIX_SHA, 'Prefix helper differs')
prefix = module(ROOT/PREFIX, 'two_track_prefix')
require, write, read, digest, now = prefix.require, prefix.write, prefix.read, prefix.digest, prefix.now

def prepare(output):
    require(not Path(output).exists(), 'Specification already exists')
    require(digest(ROOT/OLD_SPEC) == OLD_SHA, 'Prior specification differs')
    old = read(ROOT/OLD_SPEC)
    base = module(ROOT/prefix.BASE_PATH, 'two_track_base_prepare')
    require(digest(ROOT/prefix.BASE_PATH) == prefix.BASE_SHA, 'Scorer source differs')
    require(base.package_versions() == old['runtime_packages'], 'Runtime packages differ')
    require(base.artifact_receipt(Path(old['model_path'])) == old['model_artifact'], 'Model differs')
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(old['model_path'], local_files_only=True, trust_remote_code=False)
    inputs = []
    for row in design.inventory():
        prompt_ids = tokenizer.encode(row['prompt'], add_special_tokens=True)
        candidates = {}
        for key, answer in row['answers'].items():
            ids = tokenizer.encode(row['prompt'] + answer, add_special_tokens=True)
            require(ids[:len(prompt_ids)] == prompt_ids, 'Prompt/continuation tokenizer boundary changed')
            require(0 < len(prompt_ids) < len(ids) <= 512, 'Invalid or excessive sequence length')
            candidates[key] = {'input_token_ids':ids, 'prompt_token_count':len(prompt_ids),
                'candidate_token_ids':ids[len(prompt_ids):], 'continuation':answer}
        a, b = [candidates[k]['candidate_token_ids'] for k in ('a','b')]
        shared = 0
        for x,y in zip(a,b):
            if x != y:
                break
            shared += 1
        require(0 < shared < min(len(a),len(b)), 'Need nonempty shared prefix and divergent answers')
        inputs.append({**row,'candidates':candidates,'shared_prefix_token_count':shared})
    files = [prefix.BASE_PATH, PREFIX, 'scripts/contextual_emoji_two_track_v1.py',
        'scripts/run_contextual_emoji_two_track_v1.py', design.SOURCE,
        'docs/CONTEXTUAL_EMOJI_TWO_TRACK_V1.md','docs/CONTEXTUAL_EMOJI_TWO_TRACK_V1.ja.md',
        'src/glyphprobe/provenance.py','src/glyphprobe/io.py']
    spec = {key:old[key] for key in ('model_path','model_artifact','runtime_packages','python_version',
        'historical_runtime','expected_implementation_sources','scoring')}
    spec.update(protocol_id=design.PROTOCOL, created_at_utc=now(), inputs=inputs, sentinels=old['sentinels'],
        prior_specification_sha256=OLD_SHA, source_files={p:digest(ROOT/p) for p in files},
        inventory_sha256=hashlib.sha256(design.canonical(design.inventory())).hexdigest(),
        planned_pairs=1632, planned_scientific_sequence_scores=3264, planned_sentinel_forwards=32,
        planned_forward_attempts=MAX_FORWARDS, independent_scenarios=24, new_independent_scenarios=0,
        preparation={'tokenizer_class':type(tokenizer).__name__, 'tokenizer_calls':4896,
            'model_forwards':0,'downloads':0,'generation_calls':0},
        compute_policy={**prefix.POLICY,'walltime_seconds':WALL_SECONDS,'maximum_forward_attempts':MAX_FORWARDS},
        claim_ceiling='development measurement behavior; no independent human validation or causal claim')
    write(output,spec)
    return {'status':'prepared','pairs':len(inputs),'planned_forward_attempts':MAX_FORWARDS,
        'specification_sha256':digest(output),'maximum_sequence_length':max(len(c['input_token_ids']) for x in inputs for c in x['candidates'].values())}

def verify(spec_path):
    spec = read(spec_path)
    require(spec['protocol_id'] == design.PROTOCOL and len(spec['inputs']) == 1632 and len(spec['sentinels']) == 8, 'Specification count differs')
    for relative, pin in spec['source_files'].items():
        require(digest(ROOT/relative) == pin, 'Bound source changed: ' + relative)
    require(digest(ROOT/OLD_SPEC) == OLD_SHA, 'Prior specification differs')
    old = read(ROOT/OLD_SPEC)
    for key in ('sentinels','model_path','model_artifact','runtime_packages','python_version',
                'historical_runtime','expected_implementation_sources','scoring'):
        require(spec[key] == old[key], 'Pinned runtime/sentinels changed: ' + key)
    require(spec['compute_policy'] == {**prefix.POLICY,'walltime_seconds':WALL_SECONDS,'maximum_forward_attempts':MAX_FORWARDS}, 'Resource policy changed')
    fresh = design.inventory()
    require(spec['inventory_sha256'] == hashlib.sha256(design.canonical(fresh)).hexdigest(), 'Inventory identity changed')
    for expected, saved in zip(fresh,spec['inputs']):
        require(all(saved[k] == v for k,v in expected.items()), 'Saved prompt inventory changed')
        a,b = [saved['candidates'][k] for k in ('a','b')]
        n = a['prompt_token_count']
        require(n == b['prompt_token_count'] and a['input_token_ids'][:n] == b['input_token_ids'][:n], 'Unequal prompt tokens')
        for c in (a,b):
            require(c['candidate_token_ids'] == c['input_token_ids'][n:] and
                    all(type(t) is int and 0 <= t < 128256 for t in c['input_token_ids']), 'Invalid token IDs')
    return spec

def plans(spec):
    result = []
    for phase, cases in [('begin',spec['sentinels']),('development',spec['inputs']),('end',spec['sentinels'])]:
        for case in cases:
            for method in ('padded_a','padded_b'):
                result.append({'event_id':f"{phase}::{case['input_id']}::{method}", 'phase':phase,
                    'input_id':case['input_id'],'method':method,'geometry':prefix.call_geometry(case,method)})
    require(len(result) == MAX_FORWARDS and len({r['event_id'] for r in result}) == MAX_FORWARDS, 'Forward inventory differs')
    return result

def exact(a,b):
    return all(a.get(k) == b.get(k) for k in ('candidate_token_logprobs','sequence_logprob_sum',
        'shared_prediction_logits_sha256','shared_prediction_logits_shape','shared_prediction_logits_dtype',
        'logits_hash_byte_order','normalization_rectangle_shape'))

def execute(spec, scorer, before, after, emit, deadline, error=None):
    cases = {x['input_id']:x for x in spec['inputs']+spec['sentinels']}
    records, attempts, begins = [],0,{}
    for event in plans(spec):
        row = {**event,'status':'not_run','forward_attempted':False}
        if error:
            row['reason'] = error
        else:
            try:
                deadline()
                before(event)
                require(attempts < MAX_FORWARDS,'Forward cap reached')
                attempts += 1
                row['forward_attempted'] = True
                try:
                    score = scorer(cases[event['input_id']],event)
                    prefix.validate_score(score,event)
                    row.update(score,status='completed')
                    if event['phase'] != 'development':
                        require(exact(score,cases[event['input_id']]['expected_scores'][event['method']]), 'Historical sentinel differs')
                        key = event['input_id'],event['method']
                        if event['phase'] == 'begin':
                            begins[key] = score
                        else:
                            require(exact(score,begins[key]), 'End sentinel differs')
                finally:
                    after(event)
                deadline()
            except BaseException as exc:
                error = f'{type(exc).__name__}: {exc}'
                if row['status'] == 'completed':
                    row['boundary_error_after_score'] = error
                else:
                    row['status'] = 'failed' if row['forward_attempted'] else 'not_run'
                    row['reason'] = error
        row['recorded_at_utc'] = now()
        emit(row)
        records.append(row)
    return records, attempts, error

def diagnose(spec, records):
    expected = plans(spec)
    require(len(records) == len(expected), 'Missing planned rows')
    for plan,row in zip(expected,records):
        require(all(row.get(k) == v for k,v in plan.items()), 'Row identity or geometry changed')
        require(row['status'] in ('completed','failed','not_run'), 'Invalid row status')
        if row['status'] == 'completed':
            prefix.validate_score(row,plan)
    index = {r['event_id']:r for r in records}
    pairs, sentinel_ok = [],True
    for case in spec['sentinels']:
        for method in ('padded_a','padded_b'):
            a,b = [index[f"{phase}::{case['input_id']}::{method}"] for phase in ('begin','end')]
            sentinel_ok &= a['status'] == b['status'] == 'completed' and exact(a,b) and exact(a,case['expected_scores'][method])
    for case in spec['inputs']:
        a,b = [index[f"development::{case['input_id']}::padded_{key}"] for key in ('a','b')]
        done = a['status'] == b['status'] == 'completed'
        n = case['shared_prefix_token_count']
        match = done and a['candidate_token_logprobs'][:n] == b['candidate_token_logprobs'][:n] and all(
            a[k] == b[k] for k in ('shared_prediction_logits_sha256','shared_prediction_logits_shape','shared_prediction_logits_dtype','logits_hash_byte_order'))
        pairs.append({'input_id':case['input_id'],'completed':done,'prefix_exact':match,
            's_yes_minus_no':a['sequence_logprob_sum'] - b['sequence_logprob_sum'] if done else None})
    passed = all(r['status'] == 'completed' and 'boundary_error_after_score' not in r for r in records) and sentinel_ok and all(r['prefix_exact'] for r in pairs)
    return {'numerical_gate_passed':passed,'sentinels_exact':sentinel_ok,'planned_pairs':1632,
        'completed_pairs':sum(p['completed'] for p in pairs),'matching_prefixes':sum(p['prefix_exact'] for p in pairs),
        'status_counts':dict(Counter(r['status'] for r in records)),'pairs':pairs}

def run(spec_path, output):
    require(not output.exists(), 'Run output exists; never resume silently')
    spec = verify(spec_path)
    output.mkdir(parents=True,exist_ok=False)
    started = time.monotonic()
    write(output/'run_started.json',{'protocol_id':design.PROTOCOL,'pid':os.getpid(),'started_at_utc':now(),
        'specification_sha256':digest(spec_path),'source_files':spec['source_files'],'compute_policy':spec['compute_policy']})
    observations, resources = [],{}
    def deadline():
        require(time.monotonic()-started < WALL_SECONDS, 'Wall time exhausted')
    def observe(before_load=False,event=None,boundary=None):
        return prefix.resource_guard(before_load=before_load,emit=lambda obs:observations.append({**obs,
            'event_id':event['event_id'] if event else None,'boundary':boundary}))
    def implementation(value):
        write(output/'implementation_sources.json',value)
        require(value == spec['expected_implementation_sources'],'Model/mask implementation differs')
    def alarm(*_):
        raise TimeoutError('Wall time alarm')
    old_alarm = signal.signal(signal.SIGALRM,alarm)
    signal.setitimer(signal.ITIMER_REAL,WALL_SECONDS)
    records,attempts,error,torch,model,base = [],0,None,None,None,None
    try:
        try:
            observe(True,boundary='preload')
            torch,model,base = prefix.load_model(spec,observe,lambda r:write(output/'runtime.json',r),implementation,deadline,resources)
        except BaseException as exc:
            error = f'{type(exc).__name__}: {exc}'
        with (output/'forwards.jsonl').open('x') as handle:
            def emit(row):
                handle.write(json.dumps(row,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n')
                handle.flush()
                os.fsync(handle.fileno())
            records,attempts,error = execute(spec,lambda c,e:prefix.score_call(torch,model,base,c,e),
                lambda e:observe(False,e,'before'),lambda e:observe(False,e,'after'),emit,deadline,error)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,old_alarm)
        torch = resources.get('torch',torch)
        peak = None
        if torch is not None and torch.cuda.is_initialized():
            peak = {'allocated_mib':torch.cuda.max_memory_allocated()/2**20,'reserved_mib':torch.cuda.max_memory_reserved()/2**20}
            model = None
            resources.pop('model',None)
            gc.collect()
            torch.cuda.empty_cache()
        write(output/'occupancy_checks.json',{'observations':observations})
    diagnostics = diagnose(spec,records)
    write(output/'diagnostics.json',diagnostics)
    complete = diagnostics['numerical_gate_passed'] and error is None
    summary = {'protocol_id':design.PROTOCOL,'status':'completed_numerical_gate_passed' if complete else 'stopped_or_gate_failed',
        'finished_at_utc':now(),'specification_sha256':digest(spec_path),'forward_attempts':attempts,
        'planned_forward_attempts':MAX_FORWARDS,'elapsed_seconds':time.monotonic()-started,'stop_reason':error,
        'numerical_gate_passed':complete,'status_counts':diagnostics['status_counts'],'completed_pairs':diagnostics['completed_pairs'],
        'peak_torch_memory_mib':peak,'downloads':0,'generation_calls':0,'independent_scenarios':24,'new_independent_scenarios':0,
        'artifacts':{p.name:digest(p) for p in output.iterdir() if p.is_file()}}
    write(output/'run_completed.json',summary)
    return summary

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('prepare','run'))
    parser.add_argument('--specification',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    result = prepare(args.output) if args.command == 'prepare' else run(args.specification,args.output)
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if args.command == 'prepare' or result['numerical_gate_passed'] else 2

if __name__ == '__main__':
    raise SystemExit(main())
