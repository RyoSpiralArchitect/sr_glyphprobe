#!/usr/bin/env python3
"""CPU-only independent receipt arithmetic. Does not expose model choices."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def require(ok,message):
    if not ok:
        raise ValueError(message)

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    def pairs(items):
        result={}
        for k,v in items:
            require(k not in result,'Duplicate JSON key')
            result[k]=v
        return result
    def invalid(x):
        raise ValueError('Nonfinite JSON constant')
    return json.loads(Path(path).read_text(),object_pairs_hook=pairs,parse_constant=invalid)

SCORE_FIELDS=('candidate_token_logprobs','sequence_logprob_sum','shared_prediction_logits_sha256',
    'shared_prediction_logits_shape','shared_prediction_logits_dtype','logits_hash_byte_order','normalization_rectangle_shape')

def audit(spec_path,run,root=ROOT):
    spec,complete,started=read(spec_path),read(run/'run_completed.json'),read(run/'run_started.json')
    require(complete['specification_sha256']==started['specification_sha256']==digest(spec_path),'Specification provenance mismatch')
    for name,pin in complete['artifacts'].items():
        require(Path(name).name==name and digest(run/name)==pin,'Artifact hash mismatch: '+name)
    for name,pin in spec['source_files'].items():
        path=root/name
        require(path.resolve().is_relative_to(root.resolve()) and digest(path)==pin,'Source mismatch: '+name)
    require(started['source_files']==spec['source_files'],'Launch source mismatch')
    require(read(run/'runtime.json')==spec['historical_runtime'],'Runtime differs')
    require(read(run/'implementation_sources.json')==spec['expected_implementation_sources'],'Implementation differs')
    require(datetime.fromisoformat(spec['created_at_utc'])<=datetime.fromisoformat(started['started_at_utc'])<=datetime.fromisoformat(complete['finished_at_utc']),'Timestamp order differs')
    raw=(run/'forwards.jsonl').read_text()
    require(raw.endswith('\n'),'Truncated journal')
    rows=[json.loads(x) for x in raw.splitlines()]
    require(len(rows)==3296 and len({r['event_id'] for r in rows})==3296,'Forward denominator/duplicates differ')
    cases=spec['inputs']
    require(len(cases)==1632 and len({c['input_id'] for c in cases})==1632,'Pair denominator differs')
    require(Counter(c['carrier'] for c in cases)=={'emoji':576,'word':576,'absent':288,'anchor':192},'Carrier denominators differ')
    require(len({c['block_id'] for c in cases})==24 and set(Counter(c['block_id'] for c in cases).values())=={68},'Scenario denominator differs')
    planned=[]
    for phase,group in [('begin',spec['sentinels']),('development',cases),('end',spec['sentinels'])]:
        for c in group:
            for key in ('a','b'):
                planned.append((phase,c,key))
    index={}
    token_sums_checked=0
    for row,(phase,c,key) in zip(rows,planned):
        method='padded_'+key
        event=f"{phase}::{c['input_id']}::{method}"
        require(row['event_id']==event and row['phase']==phase and row['input_id']==c['input_id'] and row['method']==method,'Forward order/identity differs')
        candidate=c['candidates'][key]
        ids=candidate['input_token_ids'];n=candidate['prompt_token_count'];total=max(len(x['input_token_ids']) for x in c['candidates'].values())
        geometry={'input_token_ids':ids+[0]*(total-len(ids)),'attention_mask':[1]*len(ids)+[0]*(total-len(ids)),
            'position_ids':list(range(total)),'valid_length':len(ids),'total_length':total,'prompt_length':n,
            'candidate_token_ids':ids[n:],'predictor_positions':list(range(n-1,len(ids)-1)),
            'normalization_start':n-1,'normalization_stop':total-1,'shared_prefix_token_count':c['shared_prefix_token_count']}
        require(row['geometry']==geometry,'Geometry differs from independently reconstructed tokens')
        require(row['status'] in ('completed','failed','not_run') and type(row['forward_attempted']) is bool and
            row['forward_attempted']==(row['status']!='not_run'),'Invalid forward disposition')
        if row['status']=='completed':
            values=row['candidate_token_logprobs']
            require(len(values)==len(ids)-n and all(isinstance(v,(int,float)) and math.isfinite(v) and v<=0 for v in values),'Invalid token score')
            require(math.fsum(values)==row['sequence_logprob_sum'],'Token sum differs')
            require(row['normalization_rectangle_shape']==[total-n,128256] and
                row['shared_prediction_logits_shape']==[c['shared_prefix_token_count'],128256] and
                row['shared_prediction_logits_dtype']=='float32','Score geometry receipt differs')
            token_sums_checked+=1
        else:
            require(not any(k in row for k in SCORE_FIELDS),'Missing row contains a score')
        index[event]=row
    sentinel_exact=0
    for c in spec['sentinels']:
        for method in ('padded_a','padded_b'):
            for phase in ('begin','end'):
                row=index[f"{phase}::{c['input_id']}::{method}"]
                if row['status']=='completed' and all(row[k]==c['expected_scores'][method][k] for k in SCORE_FIELDS):
                    sentinel_exact+=1
    complete_pairs,prefix_exact=0,0
    pair_results=[]
    for c in cases:
        a,b=[index[f"development::{c['input_id']}::padded_{key}"] for key in ('a','b')]
        done=a['status']==b['status']=='completed'
        complete_pairs+=done
        n=c['shared_prefix_token_count']
        match=done and a['candidate_token_logprobs'][:n]==b['candidate_token_logprobs'][:n] and all(
            a[k]==b[k] for k in SCORE_FIELDS[2:6])
        prefix_exact+=match
        pair_results.append({'input_id':c['input_id'],'completed':done,'prefix_exact':match,
            's_yes_minus_no':a['sequence_logprob_sum']-b['sequence_logprob_sum'] if done else None})
    require(pair_results==read(run/'diagnostics.json')['pairs'],'Runner pair arithmetic differs')
    observations=read(run/'occupancy_checks.json')['observations']
    forward_observations=[o for o in observations if o['event_id'] is not None]
    before=Counter(o['event_id'] for o in forward_observations if o['boundary']=='before')
    after=Counter(o['event_id'] for o in forward_observations if o['boundary']=='after')
    guarded=all(before[r['event_id']]==after[r['event_id']]==1 for r in rows if r['forward_attempted'])
    resources_ok=all(o['status']=='allowed' and not o['observed_peer_pids'] and
        o['free_mib']>=o['minimum_free_mib'] and o['own_process_mib']<=10240 for o in observations)
    all_complete=all(r['status']=='completed' and 'boundary_error_after_score' not in r for r in rows)
    passed=all_complete and sentinel_exact==32 and prefix_exact==1632 and guarded and resources_ok and complete['stop_reason'] is None
    require(passed==complete['numerical_gate_passed'],'Completion gate disagrees')
    return {'protocol_id':'glyphprobe-two-track-v1-independent-mechanical-audit','created_at_utc':datetime.now(timezone.utc).isoformat(),
        'assessment':'qualified_development_acquisition_not_human_validation' if passed else 'not_qualified',
        'numerical_gate_passed':passed,'planned_forward_rows':3296,'forward_rows':len(rows),
        'token_sums_checked':token_sums_checked,'planned_pairs':1632,'complete_pairs':complete_pairs,
        'exact_prefix_pairs':prefix_exact,'exact_historical_sentinel_scores':sentinel_exact,
        'independent_scenarios':24,'new_independent_scenarios':0,'status_counts':dict(Counter(r['status'] for r in rows)),
        'carrier_pair_counts':dict(Counter(c['carrier'] for c in cases)),
        'guarded_before_after_every_attempt':guarded,'all_resource_observations_allowed':resources_ok,
        'elapsed_seconds':complete['elapsed_seconds'],'peak_torch_memory_mib':complete['peak_torch_memory_mib'],
        'model_choice_summaries_disclosed':False,'human_responses_read':0,'model_forwards':0,'downloads':0,
        'inputs':{'specification_sha256':digest(spec_path),'forwards_sha256':digest(run/'forwards.jsonl'),
            'completion_sha256':digest(run/'run_completed.json'),'auditor_sha256':digest(Path(__file__))}}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--specification',type=Path,required=True)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    result=audit(args.specification,args.run)
    with args.output.open('x') as f:
        json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if result['numerical_gate_passed'] else 2

if __name__=='__main__':
    raise SystemExit(main())
