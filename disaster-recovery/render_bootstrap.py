"""Render the local DR bootstrap with an explicitly reviewed immutable revision."""
import argparse
import json
from pathlib import Path
import re

def render(revision):
    if not re.fullmatch('[0-9a-f]{40}',revision):raise ValueError('A reviewed full Git commit is required')
    bundle=json.loads((Path(__file__).parent/'bootstrap.json').read_text())
    bundle['items'][-1]['spec']['source']['targetRevision']=revision
    return bundle

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True)
    print(json.dumps(render(p.parse_args().revision),indent=2))
