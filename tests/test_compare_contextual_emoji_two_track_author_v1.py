"""Synthetic arithmetic/join checks; no human or model-run files opened."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import compare_contextual_emoji_two_track_author_v1 as m


def fixture():
    assignment={'id':'synthetic','block_id':'block','family':'family','context':'p','carrier':'word','cue':'a','arm':'bounded'}
    item={'id':'synthetic','display_item':1,'prompt':'Synthetic scene',
          'questions':[{'id':'local_match','text':'Is it true that a synthetic property matches?'}],
          'response':{'abstain':False,'judgments':{'local_match':{'decidable':True,'answer':True}}},'statuses':{'local_match':'yes'}}
    cases=[]; forwards=[]; diagnostics=[]
    for polarity,s in (('positive',2.0),('negative',-3.0)):
        question='Is it '+('true' if polarity=='positive' else 'false')+' that a synthetic property matches?'
        identity='block::p::word::a::local_match::'+polarity
        answers={'a':' The answer is yes.','b':' The answer is no.'}
        cases.append({**{k:v for k,v in assignment.items() if k!='id'},'input_id':identity,'probe':'local_match','polarity':polarity,
                      'stimulus':item['prompt'],'question':question,'prompt':item['prompt']+'\nQuestion: '+question+'\nAnswer:',
                      'answers':answers,'candidates':{k:{'continuation':v} for k,v in answers.items()},'author_reference':True,'reference_status':'synthetic'})
        for method,value in (('padded_a',-5+s),('padded_b',-5.0)):
            forwards.append({'phase':'development','input_id':identity,'method':method,'status':'completed',
                             'candidate_token_logprobs':[value],'sequence_logprob_sum':value})
        diagnostics.append({'input_id':identity,'completed':True,'prefix_exact':True,'s_yes_minus_no':s})
    return item,assignment,cases,forwards,diagnostics


class TwoTrackComparisonTests(unittest.TestCase):
    def test_polarity_and_tie(self):
        self.assertTrue(m.truth(2,'positive'));self.assertTrue(m.truth(-2,'negative'))
        self.assertFalse(m.truth(2,'negative'));self.assertIsNone(m.truth(0,'negative'))
        with self.assertRaises(ValueError):m.truth(float('nan'),'positive')

    def test_exact_join_and_negative_mate(self):
        i,a,c,f,d=fixture(); model=m.describe_model(c,f,d); rows=m.join_human([i],[a],c,model)
        self.assertEqual(m.human_metrics(rows)['agreement_positive_question'],1)
        self.assertEqual(m.human_metrics(rows)['agreement_negative_wording_sensitivity_only'],1)
        self.assertEqual(rows[0]['polarity_status'],'consistent')

    def test_undecidable_not_recoded_to_no(self):
        i,a,c,f,d=fixture(); i['response']['judgments']['local_match']={'decidable':False,'answer':None}; i['statuses']['local_match']='undecidable'
        rows=m.join_human([i],[a],c,m.describe_model(c,f,d)); v=m.human_metrics(rows)
        self.assertEqual(v['human_status_counts']['undecidable'],1)
        self.assertEqual(v['comparable_binary'],0)
        self.assertEqual(v['agreement_positive_question'],0)

    def test_literal_text_and_metadata_mismatch_rejected(self):
        for key in ('prompt','question','family'):
            i,a,c,f,d=fixture(); model=m.describe_model(c,f,d)
            if key=='prompt':i['prompt']+=' changed'
            else:c[0][key]+=' changed'
            with self.assertRaises(ValueError):m.join_human([i],[a],c,model)

    def test_duplicate_missing_and_diagnostic_tamper_rejected(self):
        i,a,c,f,d=fixture()
        for cc,ff,dd in ((c+[c[0]],f,d),(c,f[:-1],d),(c,f+[f[0]],d),(c,f,d+d[:1])):
            with self.assertRaises(ValueError):m.describe_model(cc,ff,dd)
        d[0]['s_yes_minus_no']=0
        with self.assertRaises(ValueError):m.describe_model(c,f,d)

    def test_full_polarity_pair_required(self):
        i,a,c,f,d=fixture(); rows=m.describe_model(c,f,d)
        with self.assertRaises(ValueError):m.paired_polarities(rows[:-1])
        rows[-1]['normalized_truth']=False
        self.assertEqual(m.polarity_metrics(m.paired_polarities(rows))['inconsistent'],1)

    def test_contrast_sign_uses_question_polarity(self):
        rows=[]
        for pol in ('positive','negative'):
            for context,cue,s in (('p','a',2),('p','b',-1),('q','a',-2),('q','b',3)):
                rows.append({'block_id':'one','family':'one','carrier':'emoji','probe':'local_match','polarity':pol,
                             'context':context,'cue':cue,'s_yes_minus_no_nats':s if pol=='positive' else -s})
        result=m.contrasts(rows)
        self.assertEqual([r['truth_oriented_difference_of_differences_nats'] for r in result],[8,8])
        with self.assertRaises(ValueError):m.contrasts(rows[:-1])

    def test_absent_not_duplicated_and_not_in_contrast(self):
        self.assertEqual(m.contrasts([{'carrier':'absent'}]),[])

    def test_ties_excluded_only_from_binary_comparison_denominator(self):
        i,a,c,f,d=fixture(); model=m.describe_model(c,f,d)
        model[0]['normalized_truth']=None
        rows=m.join_human([i],[a],c,model); s=m.human_metrics(rows)
        self.assertEqual(s['judgments'],1);self.assertEqual(s['comparable_binary'],0)
        self.assertEqual(s['model_ties_positive_all'],1)

    def test_inputs_unchanged(self):
        i,a,c,f,d=fixture(); before=copy.deepcopy((i,a,c,f,d))
        m.join_human([i],[a],c,m.describe_model(c,f,d))
        self.assertEqual(before,(i,a,c,f,d))


if __name__=='__main__':unittest.main()
