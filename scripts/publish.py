"""Explicit optional GHCR publication after a successful local container check."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

parser=argparse.ArgumentParser()
parser.add_argument('--game',choices=['chess','uno','bluff'],required=True)
args=parser.parse_args()
reports=Path(__file__).resolve().parents[1]/'reports'/args.game
validation=json.loads((reports/'validation.json').read_text())
assert validation['passed']
image=validation['image']
current=subprocess.check_output(['docker','image','inspect',image,'--format','{{.Id}}'],text=True).strip()
assert current==validation['image_id'], 'Image changed after validation'
owner=os.environ['GITHUB_REPOSITORY_OWNER'].lower()
destination=f"ghcr.io/{owner}/hermit-{args.game}:{validation['revision']}"
subprocess.run(['docker','login','ghcr.io','-u',os.environ['GITHUB_ACTOR'],'--password-stdin'],
               input=os.environ['GHCR_TOKEN'],text=True,check=True,capture_output=True)
subprocess.run(['docker','tag',image,destination],check=True)
subprocess.run(['docker','push',destination],check=True)
digests=json.loads(subprocess.check_output(['docker','image','inspect',destination,'--format','{{json .RepoDigests}}'],text=True))
matching=[d for d in digests if d.startswith(f'ghcr.io/{owner}/hermit-{args.game}@sha256:')]
assert len(matching)==1 and re.search(r'@sha256:[0-9a-f]{64}$',matching[0])
result={'published_reference':matching[0],'source_commit':validation['revision'],
        'note':'Ensure organizers accept GHCR and have pull access; this does not register an event submission.'}
(reports/'published.json').write_text(json.dumps(result,indent=2))
with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as handle:
    handle.write('\nPublished immutable reference: `'+matching[0]+'`\n')
subprocess.run(['docker','logout','ghcr.io'],check=True,capture_output=True)
