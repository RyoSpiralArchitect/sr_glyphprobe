"""Synthetic-only tests; actual participant data and model results are excluded."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('two_track_description', ROOT/'scripts/analyze_contextual_emoji_two_track_author_v1.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def packet():
    return {'protocol_id':m.server.design.PROTOCOL,'package_id':'pkg_'+'a'*32,'language':'en','total_items':3,
            'items':[{'id':'item_'+str(i)*32, 'prompt':'Synthetic scene '+str(i), 'questions':[
                {'id':q,'text':'Synthetic '+q+'?'} for q in (['local_match'] if i == 1 else ['message_reading','outcome_evidence'])]}
                     for i in (1,2,3)]}


def response(judgments=None, abstain=False):
    return {'judgments':judgments or {},'abstain':abstain,'language_clear':None,'recognition':None,'reasons':[],'note':''}


def fixture(folder, finalize=True):
    package = folder/'package'; (package/'participant').mkdir(parents=True)
    p = packet(); participant = package/'participant/participant.json'; m.write_new(participant,p)
    manifest = {'protocol_id':p['protocol_id'],'package_id':p['package_id'],
                'generator_sha256':m.sha(ROOT/'scripts/contextual_emoji_two_track_v1.py'),
                'source_sha256':m.server.design.SOURCE_SHA, 'participant_sha256':m.sha(participant),
                'allocation':{'items':3,'primary_questions':5}}
    m.write_new(package/'manifest.json',manifest)
    binding = {'package_id':p['package_id'],'participant_sha256':m.sha(participant),'manifest_sha256':m.sha(package/'manifest.json')}
    journal_path = folder/'responses/responses.jsonl'
    j = m.server.Journal(journal_path,package,p,binding,m.server.interface_identity())
    def mutate(action, **body):
        return j.mutate(action,{'request_id':f'synthetic_{j.state["revision"]:03}',
                              'revision':j.state['revision'],'instruction_language':'ja',**body})
    mutate('setup',setup={'english_confidence':'comfortable','research_exposure':'yes','model_exposure':'no','comparison_exposure':'yes'})
    mutate('start')
    mutate('response',item_id=p['items'][0]['id'],response=response({'local_match':{'decidable':True,'answer':False}}))
    mutate('response',item_id=p['items'][0]['id'],response=response({'local_match':{'decidable':False,'answer':None}}))
    mutate('response',item_id=p['items'][1]['id'],response=response(abstain=True))
    if finalize:
        mutate('finalize',confirm=True,remaining_reason='Synthetic missing item')
    j.close()
    return package,journal_path


class TwoTrackDescriptionTests(unittest.TestCase):
    def test_readonly_replay_preserves_missing_uncertainty_and_history(self):
        with tempfile.TemporaryDirectory() as d:
            p,j = fixture(Path(d)); digest = m.sha(j)
            s,rows = m.phase_one(p,j)
            self.assertEqual(s['scene_denominators'],{'planned':3,'saved_including_abstain':2,'abstain':1,'missing':1})
            self.assertEqual(s['judgment_denominators'],{'planned':5,'decidable':0,'undecidable':1,'abstain':2,'missing':2})
            self.assertEqual(s['by_probe']['local_match']['no'],0)
            self.assertEqual(s['response_saves'],3)
            self.assertEqual(s['resaved_items'],[1])
            self.assertFalse(rows[0]['saved_history'][0]['response']['judgments']['local_match']['answer'])
            self.assertEqual(m.sha(j),digest)

    def test_no_assignment_or_model_access(self):
        with tempfile.TemporaryDirectory() as d:
            p,j = fixture(Path(d)); original = Path.read_bytes
            def guarded(path):
                if any(word in str(path) for word in ('assignment','specification','forwards','diagnostics')):
                    raise AssertionError('Concealed data read')
                return original(path)
            with patch.object(Path,'read_bytes',guarded), patch.object(m.server.Journal,'__init__',side_effect=AssertionError('Writer opened')):
                s,_ = m.phase_one(p,j)
            self.assertFalse(s['assignment_or_model_scores_opened_by_this_stage'])

    def test_missing_optional_metadata_not_imputed(self):
        with tempfile.TemporaryDirectory() as d:
            p,j = fixture(Path(d)); s,_ = m.phase_one(p,j)
            self.assertEqual(s['language_clear_counts'],{'yes':0,'no':0,'missing':3})
            self.assertEqual(s['recognition_counts']['missing'],3)
            self.assertEqual(s['items_without_reason_selection'],3)

    def test_known_exposure_not_overwritten_by_self_report(self):
        with tempfile.TemporaryDirectory() as d:
            p,j = fixture(Path(d)); s,_ = m.phase_one(p,j)
            self.assertEqual(s['setup_self_report']['model_exposure'],'no')
            self.assertTrue(s['known_participant_context']['prior_model_outcome_exposure_known'])
            self.assertEqual(s['independent_raters'],0)

    def test_incomplete_finalize_is_not_automatic(self):
        with tempfile.TemporaryDirectory() as d:
            p,j = fixture(Path(d),finalize=False); digest = m.sha(j)
            with self.assertRaisesRegex(ValueError,'finalized'):
                m.phase_one(p,j)
            self.assertEqual(digest,m.sha(j))

    def test_tampered_chain_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p,j = fixture(Path(d)); rows = j.read_bytes().splitlines(); r = json.loads(rows[-1]); r['state']['locked'] = False
            rows[-1] = json.dumps(r).encode(); j.write_bytes(b'\n'.join(rows)+b'\n')
            with self.assertRaisesRegex(ValueError,'hash chain'):
                m.phase_one(p,j)

    def test_bound_participant_and_manifest_checked(self):
        with tempfile.TemporaryDirectory() as d:
            p,j = fixture(Path(d)); f=p/'participant/participant.json'; f.write_bytes(f.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'Participant hash'):
                m.phase_one(p,j)

    def test_partial_tail_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p,j = fixture(Path(d)); j.write_bytes(j.read_bytes().rstrip(b'\n')); digest=m.sha(j)
            with self.assertRaisesRegex(ValueError,'partial'):
                m.phase_one(p,j)
            self.assertEqual(m.sha(j),digest)

    def test_output_exclusive(self):
        with tempfile.TemporaryDirectory() as d:
            p,j = fixture(Path(d)); out=Path(d)/'analysis'; m.phase_one(p,j,out)
            with self.assertRaisesRegex(ValueError,'Existing'):
                m.phase_one(p,j,out)

    def test_summarize_binary_and_naturalistic_pair(self):
        p=packet(); p['items']=p['items'][:2]; p['total_items']=2
        natural=response({'message_reading':{'decidable':True,'answer':True},'outcome_evidence':{'decidable':True,'answer':False}})
        local=response({'local_match':{'decidable':True,'answer':True}})
        records=[{'participant_identity':{}}, {'action':'start','body':{'instruction_language':'ja'},'recorded_at_utc':'2026-01-01T00:00:00+00:00'},
                 {'action':'finalize','body':{'instruction_language':'ja'},'recorded_at_utc':'2026-01-01T00:01:00+00:00',
                  'state':{'locked':True,'revision':2,'setup':{},'responses':{p['items'][0]['id']:local,p['items'][1]['id']:natural}}}]
        original=copy.deepcopy(records); s,_=m.summarize(p,records)
        self.assertEqual(s['naturalistic_joint_counts'],[{'message_reading':'yes','outcome_evidence':'no','scenes':1}])
        self.assertEqual(s['judgment_denominators']['decidable'],3)
        self.assertEqual(records,original)


if __name__ == '__main__':
    unittest.main()
