#!/usr/bin/env python3
"""Secondary, post-result token decomposition; the primary estimator is unchanged."""
import argparse
import json
import math
from pathlib import Path

import compare_contextual_emoji_two_track_author_v1 as comparison


def diagnose(cases, forwards, model_rows):
    cindex=comparison.unique(cases,'input_id')
    index={}
    for r in forwards:
        if r['phase']=='development':
            key=r['input_id'],r['method']
            comparison.require(key not in index,'Duplicate diagnostic forward')
            index[key]=r
    comparison.require(set(cindex)=={r['input_id'] for r in model_rows},'Diagnostic coverage differs')
    comparison.require(set(index)=={(i,k) for i in cindex for k in ('padded_a','padded_b')},'Diagnostic forward coverage differs')
    rows=[]; token_model=[]
    for model in model_rows:
        i=model['input_id']; c=cindex[i]
        a,b=[index[i,'padded_'+k]['candidate_token_logprobs'] for k in ('a','b')]
        ca,cb=[c['candidates'][k]['candidate_token_ids'] for k in ('a','b')]
        comparison.require(c['shared_prefix_token_count']==3 and ca==[578,4320,374,10035,13] and cb==[578,4320,374,912,13],
                           'This diagnostic requires the exact v1 five-token answers')
        comparison.require(len(a)==len(b)==5 and a[:3]==b[:3], 'Answer prefix/length differs')
        delta=math.fsum(a)-math.fsum(b); choice=a[3]-b[3]; suffix=a[4]-b[4]
        comparison.require(delta==model['s_yes_minus_no_nats'] and math.isclose(delta,choice+suffix,rel_tol=0,abs_tol=1e-12),
                           'Decomposition arithmetic differs')
        token_truth=comparison.truth(choice,model['polarity'])
        rows.append({**{k:model[k] for k in ('input_id',*comparison.DIMENSIONS)},
                     'primary_sequence_margin_nats':delta,'shared_prefix_delta_nats':0.0,
                     'yes_no_token_delta_nats':choice,'period_token_delta_nats':suffix,
                     'sequence_truth':model['normalized_truth'],'token_truth':token_truth,
                     'sign_reversal_excluding_ties':token_truth is not None and model['normalized_truth'] is not None and token_truth!=model['normalized_truth'],
                     'answer_token_tie':choice==0})
        token_model.append({**model,'s_yes_minus_no_nats':choice,'normalized_truth':token_truth,
                            'literal_answer':None if choice==0 else choice>0,
                            'truth_oriented_margin_nats':choice if model['polarity']=='positive' else -choice})
    polarities=comparison.paired_polarities(token_model)
    def metrics(group):
        return {'candidate_pairs':len(group),'sign_reversals_excluding_ties':sum(r['sign_reversal_excluding_ties'] for r in group),
                'answer_token_ties':sum(r['answer_token_tie'] for r in group),
                'mean_yes_no_token_delta_nats':sum(r['yes_no_token_delta_nats'] for r in group)/len(group),
                'mean_period_token_delta_nats':sum(r['period_token_delta_nats'] for r in group)/len(group)}
    return {'status':'secondary_post_result_diagnostic_not_replacement_estimator','all_candidate_pairs':len(rows),
            'decomposition':metrics(rows),'by_probe':comparison.grouped(rows,('probe',),metrics),
            'answer_token_polarity':comparison.polarity_metrics(polarities),
            'answer_token_anchors':comparison.grouped([r for r in token_model if r['carrier']=='anchor'],('cue','polarity'),comparison.model_metrics),
            'new_model_forwards':0,'primary_estimator_changed':False,
            'claim_ceiling':'suffix dependence diagnostic only; no validation or post-hoc score rescue'},rows


def saved_run():
    folder=comparison.ROOT/'validation/contextual_emoji_two_track_v1'
    comparison.require(all(comparison.sha(folder/n)==pin for n,pin in comparison.MODEL_FILES.items()),'Model provenance differs')
    cases=json.loads((folder/'specification.json').read_text())['inputs']
    forwards=[json.loads(line) for line in (folder/'run3296/forwards.jsonl').read_text().splitlines()]
    diagnostics=json.loads((folder/'run3296/diagnostics.json').read_text())['pairs']
    primary=comparison.describe_model(cases,forwards,diagnostics)
    summary,rows=diagnose(cases,forwards,primary)
    summary['source_hashes']={**comparison.MODEL_FILES,'diagnostic_code':comparison.sha(__file__)}
    return summary,rows


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    result,_=saved_run()
    comparison.human.helpers.private_directory(args.output.parent)
    comparison.write_new(args.output,result)
    print(json.dumps(result,indent=2))
