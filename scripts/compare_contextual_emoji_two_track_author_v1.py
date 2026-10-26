#!/usr/bin/env python3
"""Post-seal author/model comparison and full-inventory descriptive readout.

No forward calls, human-gold accuracy, inference tests, or response recoding.
All linked outputs remain private and outside Git.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
import json
import math
from pathlib import Path
import statistics

import analyze_contextual_emoji_two_track_author_v1 as human

ROOT, require, sha, write_new = human.ROOT, human.require, human.sha, human.write_new
MODEL_FILES = {
    'specification.json':'172af46ca6b4d946edbfb1daa9f2926850d8ed25559070301cdf01b548416039',
    'run3296/forwards.jsonl':'23951e81b4606b47110880d3b15d199e0cd804616860050fba4821b709f2b0a5',
    'run3296/run_completed.json':'37703e2b8d382a65436b28e38c0a080da6f98ead230ad4a99a690c8313fe8fef',
    'run3296/diagnostics.json':'c4ceedccc8a27b6e9f6d932f254a114aa742df1ff9f5e2b1f12ba6fa44b8e1fe',
}
DIMENSIONS = ('block_id','family','context','carrier','cue','arm','probe','polarity')


def unique(rows, key):
    index = {r[key]:r for r in rows}
    require(len(index) == len(rows), 'Duplicate join key: '+key)
    return index


def truth(s, polarity):
    require(math.isfinite(s) and polarity in ('positive','negative'), 'Invalid score or polarity')
    return None if s == 0 else (s > 0 if polarity == 'positive' else s < 0)


def describe_model(cases, forwards, diagnostics):
    index, saved = unique(cases,'input_id'), unique(diagnostics,'input_id')
    require(set(index) == set(saved), 'Diagnostic coverage differs')
    scores = {}
    for r in forwards:
        if r['phase'] != 'development':
            continue
        key = r['input_id'],r['method']
        require(key not in scores and r['status'] == 'completed', 'Duplicate/incomplete development forward')
        require(all(math.isfinite(x) for x in r['candidate_token_logprobs']) and
                math.fsum(r['candidate_token_logprobs']) == r['sequence_logprob_sum'], 'Token sum differs')
        scores[key] = r['sequence_logprob_sum']
    require(set(scores) == {(i,m) for i in index for m in ('padded_a','padded_b')}, 'Forward join coverage differs')
    result=[]
    for c in cases:
        i=c['input_id']; s=scores[i,'padded_a']-scores[i,'padded_b']
        require(saved[i]['completed'] and saved[i]['prefix_exact'] and saved[i]['s_yes_minus_no'] == s, 'Diagnostic arithmetic differs')
        require(c['answers'] == {'a':' The answer is yes.','b':' The answer is no.'} and
                all(c['candidates'][k]['continuation'] == c['answers'][k] for k in ('a','b')), 'Answer candidate differs')
        require(c['prompt'] == c['stimulus']+'\nQuestion: '+c['question']+'\nAnswer:', 'Prompt composition differs')
        result.append({'input_id':i, **{k:c[k] for k in DIMENSIONS},
                       's_yes_minus_no_nats':s, 'literal_answer':None if s == 0 else s > 0,
                       'normalized_truth':truth(s,c['polarity']),
                       'truth_oriented_margin_nats':s if c['polarity'] == 'positive' else -s,
                       'author_reference':c['author_reference'], 'reference_status':c['reference_status']})
    return result


def distribution(values):
    return {'n':len(values), 'mean':statistics.mean(values) if values else None,
            'median':statistics.median(values) if values else None,
            'min':min(values) if values else None, 'max':max(values) if values else None}


def model_metrics(rows):
    referenced=[r for r in rows if r['author_reference'] is not None]
    return {'candidate_pairs':len(rows), 'scenarios':len({r['block_id'] for r in rows}),
            'literal_yes':sum(r['literal_answer'] is True for r in rows),
            'literal_no':sum(r['literal_answer'] is False for r in rows),
            'ties':sum(r['normalized_truth'] is None for r in rows),
            'normalized_true':sum(r['normalized_truth'] is True for r in rows),
            'normalized_false':sum(r['normalized_truth'] is False for r in rows),
            'authored_reference_available':len(referenced),
            'authored_reference_agreement_not_accuracy':sum(r['normalized_truth'] is r['author_reference'] for r in referenced),
            'yes_minus_no_nats':distribution([r['s_yes_minus_no_nats'] for r in rows])}


def grouped(rows, fields, metric):
    groups=defaultdict(list)
    for r in rows:
        groups[tuple(r[k] for k in fields)].append(r)
    return [{**dict(zip(fields,key)),**metric(values)} for key,values in sorted(groups.items())]


def paired_polarities(rows):
    groups=defaultdict(dict)
    keys=tuple(k for k in DIMENSIONS if k != 'polarity')
    for r in rows:
        k=tuple(r[f] for f in keys)
        require(r['polarity'] not in groups[k], 'Duplicate polarity')
        groups[k][r['polarity']]=r
    result=[]
    for key,pair in sorted(groups.items()):
        require(set(pair) == {'positive','negative'}, 'Missing polarity mate')
        p,n=pair['positive'],pair['negative']
        determinate=p['normalized_truth'] is not None and n['normalized_truth'] is not None
        result.append({**dict(zip(keys,key)), 'positive_input_id':p['input_id'], 'negative_input_id':n['input_id'],
                       'positive_truth':p['normalized_truth'],'negative_truth':n['normalized_truth'],
                       'status':'consistent' if determinate and p['normalized_truth'] == n['normalized_truth'] else
                                'inconsistent' if determinate else 'tie',
                       'positive_s_nats':p['s_yes_minus_no_nats'],'negative_s_nats':n['s_yes_minus_no_nats']})
    return result


def polarity_metrics(rows):
    counts=Counter(r['status'] for r in rows)
    return {'polarity_pairs':len(rows), **{k:counts[k] for k in ('consistent','inconsistent','tie')}}


def contrasts(rows):
    groups=defaultdict(dict)
    fields=('block_id','family','carrier','probe','polarity')
    for r in rows:
        if r['carrier'] not in ('emoji','word'):
            continue
        key=tuple(r[k] for k in fields); cell=r['context'],r['cue']
        require(cell not in groups[key], 'Duplicate contrast cell')
        groups[key][cell]=r['s_yes_minus_no_nats']
    result=[]
    for key,cells in sorted(groups.items()):
        require(set(cells) == {('p','a'),('p','b'),('q','a'),('q','b')}, 'Incomplete 2x2 contrast')
        raw=(cells['p','a']-cells['p','b'])-(cells['q','a']-cells['q','b'])
        result.append({**dict(zip(fields,key)), 'literal_yes_no_difference_of_differences_nats':raw,
                       'truth_oriented_difference_of_differences_nats':raw if key[-1] == 'positive' else -raw})
    return result


def contrast_metrics(rows):
    values=[r['truth_oriented_difference_of_differences_nats'] for r in rows]
    return {**distribution(values),'positive':sum(v>0 for v in values),
            'negative':sum(v<0 for v in values),'zero':sum(v==0 for v in values)}


def human_metrics(rows):
    binary=[r for r in rows if r['human_status'] in ('yes','no')]
    comparable=[r for r in binary if r['model_positive_truth'] is not None]
    negative=[r for r in binary if r['model_negative_truth'] is not None]
    reference=[r for r in binary if r['author_reference'] is not None]
    return {'judgments':len(rows), 'scenes':len({r['id'] for r in rows}),
            'human_status_counts':{k:sum(r['human_status']==k for r in rows) for k in human.STATUSES},
            'comparable_binary':len(comparable),
            'agreement_positive_question':sum((r['human_status']=='yes') == r['model_positive_truth'] for r in comparable),
            'negative_wording_comparable_binary':len(negative),
            'agreement_negative_wording_sensitivity_only':sum((r['human_status']=='yes') == r['model_negative_truth'] for r in negative),
            'binary_authored_reference_available':len(reference),
            'author_reference_agreement_not_accuracy':sum((r['human_status']=='yes') is r['author_reference'] for r in reference),
            'polarity_inconsistent_selected_questions':sum(r['polarity_status']=='inconsistent' for r in rows),
            'model_ties_positive_all':sum(r['model_positive_truth'] is None for r in rows)}


def join_human(items, assignments, cases, model_rows):
    assignment=unique(assignments,'id'); case_index=unique(cases,'input_id'); model=unique(model_rows,'input_id')
    require({r['id'] for r in items} == set(assignment) and len(items) == len(assignment), 'Assignment coverage differs')
    require(set(model) == set(case_index), 'Model coverage differs')
    result=[]
    for item in items:
        a=assignment[item['id']]
        for q in item['questions']:
            stem='::'.join(a[k] for k in ('block_id','context','carrier','cue'))+'::'+q['id']
            ids={p:stem+'::'+p for p in ('positive','negative')}
            require(all(i in model for i in ids.values()), 'Selected input absent')
            c=case_index[ids['positive']]
            require(c['stimulus'] == item['prompt'] and c['question'] == q['text'], 'Literal human/model text differs')
            require(all(c[k] == a[k] for k in ('block_id','family','context','carrier','cue','arm')), 'Assignment metadata differs')
            p,n=model[ids['positive']],model[ids['negative']]
            negative_case=case_index[ids['negative']]
            require(negative_case['stimulus'] == item['prompt'] and
                    negative_case['question'] == 'Is it false that '+q['text'].removeprefix('Is it true that '), 'Negative mate text differs')
            status=human.answer_status(item['response'],q['id'])
            require(item['statuses'][q['id']] == status, 'Sealed human status differs')
            consistent=p['normalized_truth'] is not None and n['normalized_truth'] is not None
            result.append({'id':item['id'],'display_item':item['display_item'], **{k:a[k] for k in ('block_id','family','context','carrier','cue','arm')},
                           'probe':q['id'],'human_status':status,'model_positive_truth':p['normalized_truth'],
                           'model_negative_truth':n['normalized_truth'],'positive_s_nats':p['s_yes_minus_no_nats'],
                           'negative_s_nats':n['s_yes_minus_no_nats'],'author_reference':c['author_reference'],
                           'positive_input_id':ids['positive'],'negative_input_id':ids['negative'],
                           'polarity_status':'consistent' if consistent and p['normalized_truth'] == n['normalized_truth'] else
                                             'inconsistent' if consistent else 'tie'})
    require(len(result) == sum(len(i['questions']) for i in items), 'Human join multiplied or lost judgments')
    return result


def compare(output, package, write=False):
    output,package=Path(output),Path(package)
    parse=human.server.base.parse_json
    seal=parse((output/'phase_one_seal.json').read_bytes())
    require(set(seal['files']) == {'phase_one_summary.json','phase_one_items.json','PHASE_ONE.md','PHASE_ONE.ja.md'}, 'Unexpected sealed files')
    require(all(sha(output/n) == pin for n,pin in seal['files'].items()), 'Sealed interpretation changed')
    exposure=parse((output/'comparison_exposure.json').read_bytes())
    require(exposure['phase_one_seal_sha256'] == sha(output/'phase_one_seal.json'), 'Exposure seal binding differs')
    require(datetime.fromisoformat(exposure['opened_at_utc']) > datetime.fromisoformat(seal['sealed_at_utc']), 'Exposure precedes seal')
    human.server.design.verify_package(package)
    stage_one=parse((output/'phase_one_summary.json').read_bytes())
    require(stage_one['source_hashes']['manifest'] == sha(package/'manifest.json'), 'Package changed after human reading')
    model_root=ROOT/'validation/contextual_emoji_two_track_v1'
    require(all(sha(model_root/n) == pin for n,pin in MODEL_FILES.items()), 'Model provenance differs')
    auditor=human.load('postseal_independent_audit',ROOT/'scripts/audit_contextual_emoji_two_track_v1.py')
    mechanical=auditor.audit(model_root/'specification.json',model_root/'run3296',ROOT)
    require(mechanical['numerical_gate_passed'], 'Model numerical gate failed')
    cases=parse((model_root/'specification.json').read_bytes())['inputs']
    forwards=[parse(line) for line in (model_root/'run3296/forwards.jsonl').read_bytes().splitlines()]
    diagnostics=parse((model_root/'run3296/diagnostics.json').read_bytes())['pairs']
    model=describe_model(cases,forwards,diagnostics)
    polarities=paired_polarities(model); contrast_rows=contrasts(model)
    assignments=parse((package/'private/assignment.json').read_bytes())
    require(assignments['model_outcome_selection'] is False and assignments['seed'] == human.server.design.SEED, 'Assignment selection differs')
    items=parse((output/'phase_one_items.json').read_bytes())
    joined=join_human(items,assignments['items'],cases,model)
    summary={
        'stage':'post_seal_two_track_descriptive_comparison','human_overall':human_metrics(joined),
        'human_by_probe':grouped(joined,('probe',),human_metrics),
        'human_by_carrier_probe':grouped(joined,('carrier','probe'),human_metrics),
        'human_by_family':grouped(joined,('family',),human_metrics),
        'model_inventory':model_metrics(model),
        'model_by_carrier_probe_polarity':grouped(model,('carrier','probe','polarity'),model_metrics),
        'model_by_family_carrier_probe_polarity':grouped(model,('family','carrier','probe','polarity'),model_metrics),
        'model_anchor_by_type_polarity':grouped([r for r in model if r['carrier']=='anchor'],('cue','polarity'),model_metrics),
        'polarity_overall':polarity_metrics(polarities),
        'polarity_by_carrier_probe':grouped(polarities,('carrier','probe'),polarity_metrics),
        'polarity_anchor_by_type':grouped([r for r in polarities if r['carrier']=='anchor'],('cue',),polarity_metrics),
        'contrast_formula':'(s[p,a]-s[p,b])-(s[q,a]-s[q,b]); s=logP(yes continuation)-logP(no continuation); multiply by -1 for negative wording',
        'context_cue_contrast_by_carrier_probe_polarity':grouped(contrast_rows,('carrier','probe','polarity'),contrast_metrics),
        'source_hashes':{**MODEL_FILES,'phase_one_seal':sha(output/'phase_one_seal.json'),
                         'exposure':sha(output/'comparison_exposure.json'),'comparison_code':sha(__file__),
                         'assignment':sha(package/'private/assignment.json'),'auditor':sha(auditor.__file__)},
        'checks':{'full_mechanical_audit_reproduced':True,'full_score_recalculation':True,
                  'unique_exact_text_join':True,'human_judgment_count':len(joined),
                  'independent_scenarios':24,'new_independent_scenarios':0},
        'new_model_forwards':0,'raw_response_recoding':False,
        'claim_ceiling':'one exposed author; response-selected comparable subset; forced model answers; not accuracy, independence, significance, or causality'
    }
    artifacts={'comparison_summary.json':summary,'comparison_items.json':joined,'model_inventory_readout.json':model,
               'model_polarity_pairs.json':polarities,'model_context_cue_contrasts.json':contrast_rows}
    if write:
        human.helpers.private_directory(output)
        require(not any((output/n).exists() for n in artifacts), 'Existing comparison preserved')
        for name,value in artifacts.items():
            write_new(output/name,value)
    return summary,artifacts


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('output','package'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    summary,_=compare(args.output,args.package,write=True)
    print(json.dumps({k:summary[k] for k in ('human_overall','human_by_probe','polarity_overall','checks')},indent=2))
