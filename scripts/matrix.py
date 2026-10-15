"""Validate exact source identities before a runner clones private repositories."""
import json
import os
from pathlib import Path, PurePosixPath
import re

def load_targets(path):
    targets=json.loads(Path(path).read_text())['targets']
    assert len(targets)==3 and {t['game'] for t in targets}=={'chess','uno','bluff'}
    for target in targets:
        assert re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',target['repository'])
        assert re.fullmatch(r'[0-9a-f]{40}',target['revision']), 'Use a full commit SHA, not main'
        directory=PurePosixPath(target['directory'])
        assert not directory.is_absolute() and '..' not in directory.parts
    return {'include':targets}

if __name__=='__main__':
    matrix=load_targets('targets.json')
    with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as handle:
        handle.write('matrix='+json.dumps(matrix,separators=(',',':'))+'\n')
