import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('two_track_server',ROOT/'scripts/serve_contextual_emoji_two_track_v1.py')
s=importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)

def packet():
    return {'protocol_id':s.design.PROTOCOL,'package_id':'pkg_'+'a'*32,'language':'en','total_items':2,'items':[
        {'id':'item_'+'b'*32,'prompt':'SYNTHETIC QA — not a study item. The requested label is striped. The accurate label report is striped.',
         'questions':[{'id':'local_match','text':'Is it true that the reported label matches the requested label?'}]},
        {'id':'item_'+'c'*32,'prompt':'SYNTHETIC QA — not a study item. A message proposes a meeting next week.',
         'questions':[{'id':'message_reading','text':'Is it true that the message suggests holding a meeting?'},
                      {'id':'outcome_evidence','text':'Is it true that the message alone establishes that the meeting already happened?'}]}]}

class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.packet=packet()
        self.binding={'package_id':self.packet['package_id'],'manifest_sha256':'d'*64,'participant_sha256':hashlib.sha256(s.base.canonical(self.packet)).hexdigest()}
        self.j=s.Journal(self.root/'responses/records.jsonl',self.root/'package',self.packet,self.binding,s.interface_identity())
        self.request=0

    def tearDown(self):
        self.j.close()
        self.temp.cleanup()

    def mutate(self,action,**payload):
        self.request+=1
        return self.j.mutate(action,{'request_id':f'request_{self.request:08d}','revision':self.j.state['revision'],'instruction_language':'ja',**payload})

    def start(self):
        self.mutate('setup',setup={'english_confidence':'comfortable','research_exposure':'yes','model_exposure':'yes','comparison_exposure':'yes'})
        self.mutate('start')

    def response(self,**updates):
        return {'judgments':{'local_match':{'decidable':True,'answer':False}},'abstain':False,
            'language_clear':None,'recognition':None,'reasons':[],'note':'',**updates}

    def test_no_answers_on_get_snapshot(self):
        self.assertFalse(self.j.snapshot()['started'])
        self.assertEqual(self.j.snapshot()['responses'],{})

    def test_undecided_distinct_from_no(self):
        self.start()
        self.mutate('response',item_id=self.packet['items'][0]['id'],response=self.response())
        first=copy.deepcopy(self.j.state['responses'])
        self.mutate('response',item_id=self.packet['items'][0]['id'],response=self.response(judgments={'local_match':{'decidable':False,'answer':None}}))
        self.assertFalse(next(iter(first.values()))['judgments']['local_match']['answer'])
        self.assertIsNone(next(iter(self.j.state['responses'].values()))['judgments']['local_match']['answer'])

    def test_undecidable_with_binary_answer_rejected(self):
        with self.assertRaises(s.base.APIError):
            self.j._response(self.response(judgments={'local_match':{'decidable':False,'answer':False}}))

    def test_decidable_without_answer_rejected(self):
        with self.assertRaises(s.base.APIError):
            self.j._response(self.response(judgments={'local_match':{'decidable':True,'answer':None}}))

    def test_question_set_must_match_item(self):
        self.start()
        with self.assertRaises(s.base.APIError):
            self.mutate('response',item_id=self.packet['items'][1]['id'],response=self.response())

    def test_abstention_is_separate_and_no_fabricated_judgments(self):
        self.start()
        self.mutate('response',item_id=self.packet['items'][0]['id'],response=self.response(judgments={},abstain=True))
        saved=next(iter(self.j.state['responses'].values()))
        self.assertTrue(saved['abstain'])
        self.assertEqual(saved['judgments'],{})
        with self.assertRaises(s.base.APIError):
            self.mutate('response',item_id=self.packet['items'][0]['id'],response=self.response(abstain=True))

    def test_natural_questions_can_disagree(self):
        self.start()
        judgment={'message_reading':{'decidable':True,'answer':True},'outcome_evidence':{'decidable':True,'answer':False}}
        self.mutate('response',item_id=self.packet['items'][1]['id'],response=self.response(judgments=judgment))
        self.assertEqual(next(iter(self.j.state['responses'].values()))['judgments'],judgment)

    def test_setup_separates_exposures_known_history_kept(self):
        self.mutate('setup',setup={'english_confidence':'comfortable','research_exposure':'no','model_exposure':'no','comparison_exposure':'no'})
        export=self.j.export()
        self.assertTrue(export['participant_identity']['prior_pilot_comparison_exposure_known'])
        self.assertEqual(export['state']['setup']['comparison_exposure'],'no')

    def test_missing_setup_field_rejected(self):
        with self.assertRaises(s.base.APIError):
            self.mutate('setup',setup={'english_confidence':'comfortable','research_exposure':'yes','model_exposure':'yes'})

    def test_finalize_missing_reason_then_lock_replay(self):
        self.start()
        with self.assertRaises(s.base.APIError):
            self.mutate('finalize',confirm=True,remaining_reason='')
        self.mutate('finalize',confirm=True,remaining_reason='Synthetic QA; intentionally missing.')
        expected=self.j.snapshot()
        self.j.close()
        self.j=s.Journal(self.root/'responses/records.jsonl',self.root/'package',self.packet,self.binding,s.interface_identity())
        self.assertEqual(self.j.snapshot(),expected)
        with self.assertRaises(s.base.APIError):
            self.mutate('response',item_id=self.packet['items'][0]['id'],response=self.response())

    def test_idempotent_mutation(self):
        self.start()
        body={'request_id':'same_request','revision':self.j.state['revision'],'instruction_language':'ja',
            'item_id':self.packet['items'][0]['id'],'response':self.response()}
        first=self.j.mutate('response',body)
        size=self.j.path.stat().st_size
        self.assertEqual(self.j.mutate('response',body),first)
        self.assertEqual(size,self.j.path.stat().st_size)

    def test_private_schema_rejected(self):
        p=copy.deepcopy(self.packet)
        p['items'][0]['answer']=True
        with self.assertRaises(ValueError):
            s.validate_packet(p)

    def test_server_receipt_binds_both_engine_and_adapter(self):
        expected=hashlib.sha256(s.base.canonical({'engine':s.BASE_SHA,'adapter':s.design.sha(Path(s.__file__))})).hexdigest()
        self.assertEqual(s.interface_identity()['server'],expected)

if __name__=='__main__':
    unittest.main()
