"""Observe the supplied process handling SIGTERM in a disposable practice Pod."""
import json,os,subprocess,time

def command(*args, data=None):
    return subprocess.run(['kubectl',*args],input=data,text=True,check=True,capture_output=True).stdout
subprocess.run(['kubectl','delete','pod','termination-proof','--ignore-not-found','--wait=true'],check=True)
pod={'apiVersion':'v1','kind':'Pod','metadata':{'name':'termination-proof','namespace':'dispatch','labels':{'dockyard-proof':'termination'}},'spec':{'restartPolicy':'Never','automountServiceAccountToken':False,'terminationGracePeriodSeconds':20,'containers':[{'name':'api','image':os.environ['DOCKYARD_IMAGE'],'imagePullPolicy':'Never','resources':{'requests':{'cpu':'10m','memory':'32Mi'},'limits':{'cpu':'200m','memory':'128Mi'}},'readinessProbe':{'httpGet':{'path':'/healthz','port':8080},'periodSeconds':1}}]}}
command('apply','-f','-',data=json.dumps(pod))
command('wait','--for=condition=Ready','pod/termination-proof','--timeout=60s')
command('exec','termination-proof','--','python','-c','import os,signal; os.kill(1,signal.SIGTERM)')
deadline=time.monotonic()+30
while time.monotonic()<deadline:
    observed=json.loads(command('get','pod','termination-proof','-o','json'))
    statuses=observed.get('status',{}).get('containerStatuses',[])
    ended=statuses[0].get('state',{}).get('terminated') if statuses else None
    if ended:
        if ended['exitCode']!=0:raise SystemExit('The process did not exit successfully after SIGTERM.')
        print('SIGTERM produced a clean exit. Inspect kubectl logs termination-proof for the event.')
        break
    time.sleep(.5)
else:raise SystemExit('The process did not terminate within its allotted grace window.')
