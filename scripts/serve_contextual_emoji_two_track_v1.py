#!/usr/bin/env python3
"""Local v1 workbench; reuse the pinned journal/HTTP engine without editing v0."""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
def load(relative,name):
    spec = importlib.util.spec_from_file_location(name,ROOT/relative)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

BASE_PATH = ROOT/'scripts/serve_contextual_emoji_author_pilot_v0.py'
BASE_SHA = '9971ce07d536d85bc0ac963344b06101bcc3fbca696682855a5b157fcbf832b2'
if hashlib.sha256(BASE_PATH.read_bytes()).hexdigest() != BASE_SHA:
    raise ValueError('Journal/HTTP engine differs')
base = load('scripts/serve_contextual_emoji_author_pilot_v0.py','two_track_journal_engine')
design = load('scripts/contextual_emoji_two_track_v1.py','two_track_packet')
base.JOURNAL_PROTOCOL = 'glyphprobe-two-track-development-journal-v1'
base.COOKIE = 'glyphprobe_two_track_v1'
base.PARTICIPANT_IDENTITY = {'pseudonym':'author-01','role':'author',
    'prior_model_outcome_exposure_known':True,'prior_pilot_comparison_exposure_known':True,
    'independent_human_validation':False}
EXPOSURE = {'yes','no','unsure','prefer_not_to_say'}
REASONS = {'cue_meaning','report_reliability','missing_context','wording','other'}
ASSETS = ROOT/'web/author-pilot-v1'

def validate_packet(packet):
    base.require(set(packet)=={'protocol_id','package_id','language','total_items','items'},'Invalid packet fields')
    base.require(packet['protocol_id']==design.PROTOCOL and packet['language']=='en','Invalid protocol/language')
    base.require(re.fullmatch(r'pkg_[a-f0-9]{32}',packet['package_id']) is not None,'Invalid package ID')
    base.require(type(packet['total_items']) is int and 0 < packet['total_items'] <= 1000 and
        len(packet['items'])==packet['total_items'],'Invalid item count')
    identities=set()
    for item in packet['items']:
        base.require(set(item)=={'id','prompt','questions'} and isinstance(item['prompt'],str) and item['prompt'], 'Invalid item')
        base.require(re.fullmatch(r'item_[a-f0-9]{32}',item['id']) is not None and item['id'] not in identities,'Invalid item ID')
        identities.add(item['id'])
        base.require(isinstance(item['questions'],list) and len(item['questions']) in (1,2),'Invalid question count')
        base.require([q['id'] for q in item['questions']] in (['local_match'],['message_reading','outcome_evidence']), 'Invalid question IDs')
        for q in item['questions']:
            base.require(set(q)=={'id','text'} and isinstance(q['text'],str) and q['text'],'Invalid question')

def interface_identity(assets=ASSETS,root=ROOT):
    assets,root=Path(assets),Path(root)
    files={'index.html':assets/'index.html','app.js':assets/'app.js','style.css':assets/'style.css',
        'protocol_en':root/'docs/CONTEXTUAL_EMOJI_TWO_TRACK_V1.md','protocol_ja':root/'docs/CONTEXTUAL_EMOJI_TWO_TRACK_V1.ja.md'}
    for path in [*files.values(),BASE_PATH,Path(__file__)]:
        base.require(path.is_file() and not path.is_symlink(),'Missing or linked interface file')
    return {'server':hashlib.sha256(base.canonical({'engine':BASE_SHA,'adapter':design.sha(Path(__file__))})).hexdigest(),
        **{k:design.sha(p) for k,p in files.items()}}

# Only this imported module instance changes; the v0 source/process remains untouched.
base.validate_public_packet=validate_packet
base.interface_identity=interface_identity

class Journal(base.Journal):
    def _transition(self,action,body,timestamp):
        if action=='setup':
            fields={'request_id','revision','instruction_language','setup'}
            if set(body)!=fields or body['instruction_language'] not in ('ja','en'):
                raise base.APIError('invalid_fields','Invalid setup fields/language.')
            if type(body['revision']) is not int or body['revision']!=self.state['revision']:
                raise base.APIError('revision_conflict','Reload the current state before saving.',409)
            if self.state['locked'] or self.state['started']:
                raise base.APIError('locked','Setup is fixed once the batch starts.',409)
            value=body['setup']
            expected={'english_confidence','research_exposure','model_exposure','comparison_exposure'}
            if not isinstance(value,dict) or set(value)!=expected or value['english_confidence'] not in (
                'comfortable','sometimes_difficult','difficult','prefer_not_to_say') or any(value[k] not in EXPOSURE for k in expected-{'english_confidence'}):
                raise base.APIError('invalid_setup','Complete the four setup questions.')
            result=copy.deepcopy(self.state)
            result['setup']=copy.deepcopy(value)
            result['revision']+=1
            return result
        if action=='response' and isinstance(body.get('item_id'),str) and body['item_id'] in self.items:
            item=next(x for x in self.packet['items'] if x['id']==body['item_id'])
            response=self._response(body.get('response'))
            expected={q['id'] for q in item['questions']}
            if set(response['judgments']) != (set() if response['abstain'] else expected):
                raise base.APIError('missing_judgment','Record each question, or explicitly abstain.')
        return super()._transition(action,body,timestamp)

    @staticmethod
    def _response(value):
        fields={'judgments','abstain','language_clear','recognition','reasons','note'}
        if not isinstance(value,dict) or set(value)!=fields or type(value['abstain']) is not bool:
            raise base.APIError('invalid_response','Invalid response fields.')
        judgments=value['judgments']
        if not isinstance(judgments,dict):
            raise base.APIError('invalid_response','Judgments must be a mapping.')
        for key,j in judgments.items():
            if key not in {'local_match','message_reading','outcome_evidence'} or not isinstance(j,dict) or set(j)!={'decidable','answer'} or type(j['decidable']) is not bool or (
                type(j['answer']) is not bool if j['decidable'] else j['answer'] is not None):
                raise base.APIError('invalid_judgment','Undecidable is null; decidable needs Yes or No.')
        if value['language_clear'] is not None and type(value['language_clear']) is not bool:
            raise base.APIError('invalid_language_clear','Language clarity must be Yes/No or missing.')
        if value['recognition'] is not None and value['recognition'] not in base.RECOGNITION:
            raise base.APIError('invalid_recognition','Invalid recognition option.')
        if not isinstance(value['reasons'],list) or any(not isinstance(x,str) or x not in REASONS for x in value['reasons']) or len(set(value['reasons']))!=len(value['reasons']):
            raise base.APIError('invalid_reasons','Invalid or duplicate reason.')
        if not isinstance(value['note'],str) or len(value['note'])>4000:
            raise base.APIError('invalid_note','Keep the note within 4,000 characters.')
        return copy.deepcopy(value)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package',type=Path,required=True)
    p.add_argument('--journal',type=Path,required=True)
    p.add_argument('--port',type=int,default=8878)
    args=p.parse_args()
    base.require(1024 <= args.port <= 65535,'Invalid port')
    packet,binding=design.verify_package(args.package)
    journal=Journal(args.journal,args.package,packet,binding,interface_identity())
    try:
        server=base.PilotServer(journal,ASSETS,args.port)
        print(f'http://127.0.0.1:{server.server_port}/ ({packet["total_items"]} scenes; development only)',flush=True)
        try:
            server.serve_forever(poll_interval=0.25)
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
    finally:
        journal.close()

if __name__=='__main__':
    main()
