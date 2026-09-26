"""Rehearse a worker drain while observing requests through the real Service."""
import json,os,subprocess,threading,time,urllib.request
from datetime import datetime,timezone
from pathlib import Path

def command(*args):
    result=subprocess.run(['kubectl',*args],text=True,capture_output=True)
    if result.returncode:raise RuntimeError(result.stderr or result.stdout)
    return result.stdout
pods=json.loads(command('get','pods','-l','app=dispatch,track=stable','-o','json'))['items']
pods=[p for p in pods if not p['metadata'].get('deletionTimestamp')]
if len(pods)!=4:raise SystemExit('Scale to four healthy API replicas before the drain rehearsal.')
nodes=json.loads(command('get','nodes','-l','dockyard.pool=apps','-o','json'))['items']
if len(nodes)<2:raise SystemExit('The rehearsal needs two dedicated application workers.')
target=nodes[0]['metadata']['name'];before=[p['metadata']['uid'] for p in pods if p['spec']['nodeName']==target]
if not before:raise SystemExit('The chosen worker has no API Pods to move.')
samples=[];errors=[];stop=threading.Event();start=datetime.now(timezone.utc).isoformat()
def observe():
    while not stop.is_set():
        try:
            with urllib.request.urlopen('http://127.0.0.1:'+os.environ['DOCKYARD_PORT']+'/readyz',timeout=2) as response:
                samples.append(response.status==200 and json.load(response).get('ready') is True)
        except Exception as error:
            samples.append(False)
            errors.append({"time":datetime.now(timezone.utc).isoformat(),"type":type(error).__name__,"message":str(error)})
        stop.wait(.2)
thread=threading.Thread(target=observe);thread.start()
try:
    command('drain',target,'--ignore-daemonsets','--delete-emptydir-data','--timeout=90s')
    time.sleep(3)
finally:
    command('uncordon',target)
    stop.set();thread.join(timeout=4)
command('rollout','status','deployment/dispatch','--timeout=120s')
subprocess.run(['python','wait-scale.py'],check=True)
record={'lab':os.environ['DOCKYARD_LAB'],'node':target,'started_at':start,'finished_at':datetime.now(timezone.utc).isoformat(),'before_uids':before,'samples':len(samples),'failures':sum(not sample for sample in samples),'errors':errors}
Path('drain-evidence.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
if len(samples)<5 or not all(samples):raise SystemExit('The drain interrupted readiness. Inspect placement, budgets, and dependencies before retrying.')
