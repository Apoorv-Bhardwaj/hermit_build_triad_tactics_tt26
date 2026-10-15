"""External checker driver. Mounted read-only, never copied into the image."""
from pathlib import Path
import importlib.util
import json
import sys

sys.path.insert(0,'/app')
spec=importlib.util.spec_from_file_location('chess_sdk.external_check','/checks/check.py')
fixture=importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
manifest=json.loads(Path('/checks/submission.json').read_text())
original=fixture.initial
def initial(colour):
    value=original(colour)
    value['harness_config']=manifest['harness_config']
    return value
fixture.initial=initial
passed=True
for colour in ['white','black']:
    result=fixture.check_harness([sys.executable,'-m','chess_sdk','run','--agent','agent:choose'],colour=colour)
    print(json.dumps({'colour':colour,**result},indent=2),flush=True)
    passed=passed and result['passed']
raise SystemExit(0 if passed else 1)
