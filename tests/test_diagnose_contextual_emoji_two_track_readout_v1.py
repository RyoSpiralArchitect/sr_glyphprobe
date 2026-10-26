"""Synthetic post-result decomposition checks; no live evidence."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import diagnose_contextual_emoji_two_track_readout_v1 as m


class DecompositionTests(unittest.TestCase):
    def fixture(self):
        cases=[]; forwards=[]; model=[]
        for pol in ('positive','negative'):
            c={'input_id':pol,'shared_prefix_token_count':3,'candidates':{
                'a':{'candidate_token_ids':[578,4320,374,10035,13]},'b':{'candidate_token_ids':[578,4320,374,912,13]}}}
            cases.append(c)
            for k,v in (('a',[-1,-1,-1,-1,-3]),('b',[-1,-1,-1,-2,-1])):
                forwards.append({'phase':'development','input_id':pol,'method':'padded_'+k,'candidate_token_logprobs':v})
            model.append({'input_id':pol,'block_id':'one','family':'one','context':'p','carrier':'emoji','cue':'a','arm':'bounded',
                          'probe':'local_match','polarity':pol,'s_yes_minus_no_nats':-1,
                          'normalized_truth':m.comparison.truth(-1,pol),'author_reference':True,'reference_status':'synthetic'})
        return cases,forwards,model

    def test_period_can_reverse_choice_without_changing_primary(self):
        c,f,r=self.fixture(); result,rows=m.diagnose(c,f,r)
        self.assertEqual(result['decomposition']['sign_reversals_excluding_ties'],2)
        self.assertEqual(rows[0]['yes_no_token_delta_nats'],1)
        self.assertEqual(rows[0]['period_token_delta_nats'],-2)
        self.assertFalse(result['primary_estimator_changed'])

    def test_prefix_mismatch_rejected(self):
        c,f,r=self.fixture();f[0]['candidate_token_logprobs'][0]=-2
        with self.assertRaises(ValueError):m.diagnose(c,f,r)

    def test_token_geometry_rejected(self):
        c,f,r=self.fixture();c[0]['candidates']['a']['candidate_token_ids'][-1]=42
        with self.assertRaises(ValueError):m.diagnose(c,f,r)

    def test_score_disagreement_rejected(self):
        c,f,r=self.fixture();r[0]['s_yes_minus_no_nats']=42
        with self.assertRaises(ValueError):m.diagnose(c,f,r)


if __name__=='__main__':unittest.main()
