"""Build/test the committed source. No Git modifications or publishing."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

BASE=Path(__file__).resolve().parents[1]

def command(args, log, timeout=600):
    result=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=timeout)
    log.write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
    print(result.stdout,flush=True)
    print(result.stderr,file=sys.stderr,flush=True)
    if result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}); see {log.name}')
    return result.stdout

def main(args):
    reports=BASE/'reports'/args.game
    reports.mkdir(parents=True,exist_ok=True)
    result={'game':args.game,'passed':False,'repository':args.repository,'revision':args.revision,
            'limits':['Fake-model Chess check, not real organizer serving or strength.',
                      'Build/check only; no event submission or publication performed.']}
    try:
        checkout=Path(args.checkout).resolve()
        source=(checkout/args.directory).resolve()
        assert source.is_relative_to(checkout), 'Source directory escapes checkout'
        head=command(['git','-C',checkout,'rev-parse','HEAD'],reports/'commit.log').strip()
        assert head==args.revision, 'Checkout is not the configured exact commit'
        manifest=json.loads((source/'submission.json').read_text())
        assert manifest.get('team_name',manifest.get('harness_config',{}).get('team_name'))=='Hermit'
        assert (source/'Dockerfile').is_file()
        parent='python:3.12-slim-bookworm' if args.game=='chess' else 'python:3.11-slim'
        image='hermit-'+args.game
        command(['docker','pull','--platform','linux/amd64',parent],reports/'pull.log')
        # A clean context cannot upload this repository's tools or read token.
        command(['docker','build','--platform','linux/amd64','--network=none','--pull=false',
                 '--label','org.opencontainers.image.revision='+head,
                 '--label','org.opencontainers.image.source=https://github.com/'+os.environ.get('GITHUB_REPOSITORY',''),
                 '-t',image,source],reports/'build.log')
        metadata=json.loads(command(['docker','image','inspect',image],reports/'image.json'))[0]
        assert metadata['Os']=='linux' and metadata['Architecture']=='amd64'
        user='65532:65532' if args.game=='chess' else '10000:10000'
        assert metadata['Config']['User']==user, 'Wrong image USER'
        if args.game!='chess':
            assert metadata['Size']<=1610612736, 'Image exceeds 1.5 GiB'
            labels=metadata['Config'].get('Labels',{})
            prefix='org.triad-'+args.game+'.'
            assert labels[prefix+'protocol']=='1.0' and labels[prefix+'runtime']=='2'
            assert labels[prefix+'gpu']=='false' and labels[prefix+'gpu-bytes']=='0'
            assert metadata['Config']['Entrypoint']==['python','src/agent.py']
        checks=BASE/'checkers'/args.game
        # Manifest goes beside checker copies, never into the source checkout.
        check_mount=reports/'checker_mount'
        shutil.copytree(checks,check_mount,dirs_exist_ok=True)
        (check_mount/'submission.json').write_text(json.dumps(manifest))
        chess=args.game=='chess'
        memory='512m' if chess else '1g'
        test=['/checks/check.py','--agent','python','--root','/app'] if args.game=='uno' else ['/checks/driver.py']
        command(['docker','run','--rm','--network=none','--read-only','--user',user,'--cap-drop=ALL',
                 '--security-opt=no-new-privileges:true','--cpus=1','--memory',memory,'--memory-swap',memory,
                 '--pids-limit','64' if chess else '128','--ipc=none',
                 '--tmpfs','/tmp:rw,noexec,nosuid,nodev,size='+('64m' if chess else '1g')+',mode=1777',
                 '--mount','type=bind,source='+str(check_mount)+',target=/checks,readonly',
                 '--entrypoint','python',image,*test],reports/'protocol.log',timeout=180)
        # Checkers/logs are not needed in uploaded report artifacts.
        shutil.rmtree(check_mount)
        assert not command(['git','-C',checkout,'status','--porcelain'],reports/'source_status.log').strip()
        result.update(passed=True,image=image,image_id=metadata['Id'],image_bytes=metadata['Size'])
    except Exception as error:
        result['error']=str(error)
        raise
    finally:
        (reports/'validation.json').write_text(json.dumps(result,indent=2))
        summary=os.environ.get('GITHUB_STEP_SUMMARY')
        if summary:
            with open(summary,'a') as handle:
                handle.write(f"\n{args.game}: {'PASSED' if result['passed'] else 'FAILED'}; source `{args.repository}@{args.revision}`.\n")

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--game',choices=['chess','uno','bluff'],required=True)
    for name in ['checkout','directory','revision','repository']:
        parser.add_argument('--'+name,required=True)
    main(parser.parse_args())
