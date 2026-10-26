"""UI QA only. Never receives the real participant package or human answers."""
import argparse
import hashlib
from pathlib import Path
from test_serve_contextual_emoji_two_track_v1 import packet,s

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--port',type=int,default=8891)
    args=p.parse_args()
    args.output.mkdir(mode=0o700,parents=True,exist_ok=False)
    s.base.PARTICIPANT_IDENTITY={'pseudonym':'synthetic-qa','role':'synthetic','independent_human_validation':False}
    data=packet()
    binding={'package_id':data['package_id'],'participant_sha256':hashlib.sha256(s.base.canonical(data)).hexdigest(),'manifest_sha256':'d'*64}
    journal=s.Journal(args.output/'responses.jsonl',args.output/'unused-package',data,binding,s.interface_identity())
    server=s.base.PilotServer(journal,s.ASSETS,args.port)
    print(f'SYNTHETIC ONLY http://127.0.0.1:{server.server_port}/',flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()
        journal.close()
