import copy
from collections import Counter
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    spec = importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m
d = load('contextual_emoji_two_track_v1')
r = load('run_contextual_emoji_two_track_v1')

class DesignTests(unittest.TestCase):
    def setUp(self):
        self.rows = d.inventory()

    def test_full_inventory(self):
        self.assertEqual(len(self.rows),1632)
        self.assertEqual(len({x['input_id'] for x in self.rows}),1632)
        self.assertEqual(len({x['block_id'] for x in self.rows}),24)
        self.assertEqual(Counter(x['carrier'] for x in self.rows),{'emoji':576,'word':576,'absent':288,'anchor':192})

    def test_every_scenario_same_grid(self):
        for block in {x['block_id'] for x in self.rows}:
            rows = [x for x in self.rows if x['block_id']==block]
            self.assertEqual(len(rows),68)
            self.assertEqual(Counter(x['polarity'] for x in rows),{'positive':34,'negative':34})

    def test_no_human_gold_natural(self):
        self.assertTrue(all(x['author_reference'] is None for x in self.rows if x['arm']=='naturalistic'))
        self.assertTrue(all(x['author_reference'] is None for x in self.rows if x['carrier']=='absent'))

    def test_logical_anchors_balance(self):
        anchors=[x for x in self.rows if x['carrier']=='anchor']
        self.assertEqual(Counter(x['author_reference'] for x in anchors),{True:96,False:96})
        for x in anchors:
            self.assertNotIn('[no cue provided]',x['prompt'])

    def test_bounded_affect_construct_explicit(self):
        rows = [x for x in self.rows if x['block_id']=='affect_01' and x['carrier']=='word']
        self.assertTrue(all('visible facial expression' in x['prompt'] for x in rows if x['arm']=='bounded'))
        self.assertTrue(any('conveys pleasure' in x['prompt'] for x in rows if x['probe']=='message_reading'))

    def test_same_answers_all_prompts(self):
        self.assertTrue(all(x['answers']=={'a':' The answer is yes.','b':' The answer is no.'} for x in self.rows))

    def test_package_balanced_no_repeat_no_keys(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'packet'
            d.package(out)
            packet,binding=d.verify_package(out)
            assignment=json.loads((out/'private/assignment.json').read_text())['items']
            self.assertEqual(len({a['block_id'] for a in assignment}),24)
            self.assertEqual(sum(len(i['questions']) for i in packet['items']),36)
            for family in {a['family'] for a in assignment}:
                a=[x for x in assignment if x['family']==family]
                self.assertEqual(len({(x['arm'],x['carrier']) for x in a}),4)
                self.assertEqual(len({(x['context'],x['cue']) for x in a}),4)
            for item in packet['items']:
                self.assertEqual(set(item),{'id','prompt','questions'})
            self.assertEqual((out/'participant/participant.json').stat().st_mode & 0o777,0o600)

    def test_source_only_assignment_deterministic(self):
        with tempfile.TemporaryDirectory() as t:
            for name in ('a','b'):
                d.package(Path(t)/name)
            a,b=[json.loads((Path(t)/n/'private/assignment.json').read_text())['items'] for n in ('a','b')]
            self.assertEqual([{k:v for k,v in x.items() if k!='id'} for x in a], [{k:v for k,v in x.items() if k!='id'} for x in b])

    def test_never_overwrite_package(self):
        with tempfile.TemporaryDirectory() as t:
            d.package(Path(t)/'packet')
            with self.assertRaises(ValueError):
                d.package(Path(t)/'packet')

    def test_tampered_packet_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'packet'
            d.package(out)
            with (out/'participant/participant.json').open('a') as f:
                f.write(' ')
            with self.assertRaises(ValueError):
                d.verify_package(out)

class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.events=[{'event_id':str(i),'input_id':'synthetic','phase':'development','method':'padded_a','geometry':{}} for i in range(3)]
        self.spec={'inputs':[{'input_id':'synthetic'}],'sentinels':[]}

    def test_contention_before_forward_preserves_missingness(self):
        emitted=[]
        with patch.object(r,'plans',return_value=self.events):
            records,n,error=r.execute(self.spec,lambda *a:self.fail('forward must not happen'),
                lambda *a:(_ for _ in ()).throw(ValueError('other PID')),lambda *a:None,emitted.append,lambda:None)
        self.assertEqual(n,0)
        self.assertEqual([x['status'] for x in records],['not_run']*3)
        self.assertIn('other PID',error)

    def test_failed_forward_runs_after_guard_then_stops(self):
        after=[]
        with patch.object(r,'plans',return_value=self.events):
            records,n,error=r.execute(self.spec,lambda *a:(_ for _ in ()).throw(RuntimeError('failure')),
                lambda *a:None,after.append,lambda *a:None,lambda:None)
        self.assertEqual(n,1)
        self.assertEqual(len(after),1)
        self.assertEqual([x['status'] for x in records],['failed','not_run','not_run'])

    def test_after_contention_retains_score_but_blocks_gate(self):
        with patch.object(r,'plans',return_value=self.events),patch.object(r.prefix,'validate_score'):
            records,n,error=r.execute(self.spec,lambda *a:{'sequence_logprob_sum':-1.0},lambda *a:None,
                lambda *a:(_ for _ in ()).throw(ValueError('contention')),lambda *a:None,lambda:None)
        self.assertEqual(n,1)
        self.assertIn('boundary_error_after_score',records[0])
        self.assertEqual(records[1]['status'],'not_run')

    def test_preload_failure_no_forward(self):
        with patch.object(r,'plans',return_value=self.events):
            records,n,error=r.execute(self.spec,lambda *a:self.fail(),lambda *a:self.fail(),lambda *a:self.fail(),lambda *a:None,lambda:None,'preload blocked')
        self.assertEqual(n,0)
        self.assertEqual(len(records),3)

    def test_historical_geometry_and_sentinels(self):
        old=r.read(ROOT/r.OLD_SPEC)
        for c in old['sentinels']:
            a,b=[r.prefix.call_geometry(c,m) for m in ('padded_a','padded_b')]
            self.assertEqual(a['total_length'],b['total_length'])
            self.assertEqual(a['normalization_stop'],b['normalization_stop'])
            self.assertTrue(r.exact(c['expected_scores']['padded_a'],c['expected_scores']['padded_a']))

if __name__ == '__main__':
    unittest.main()
