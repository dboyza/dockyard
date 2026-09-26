"""Measure a bounded window of real service reads from inside the Pod network."""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

name = sys.argv[1] if len(sys.argv) > 1 else 'after'
if name not in {'before', 'after'}:
    raise SystemExit('Use before or after as the observation name.')
client = '''import json,time,urllib.request
samples=[]
for _ in range(20):
    start=time.perf_counter()
    try:
        with urllib.request.urlopen('http://dispatch:8080/jobs',timeout=3) as response:
            payload=json.load(response)
            samples.append({'seconds':time.perf_counter()-start,'status':response.status,'request_id':response.headers.get('X-Request-ID'),'valid':isinstance(payload.get('jobs'),list)})
    except Exception as error:samples.append({'seconds':time.perf_counter()-start,'status':0,'request_id':None,'valid':False,'error':type(error).__name__})
    time.sleep(.1)
print(json.dumps(samples))
'''
started = datetime.now(timezone.utc).isoformat()
result = subprocess.run(['kubectl', 'exec', 'deployment/dispatch', '-c', 'api', '--', 'python', '-c', client], capture_output=True, text=True, check=True)
samples = json.loads(result.stdout)
policy = json.loads(Path('slo.json').read_text())
good = sum(s['valid'] and s['status'] == 200 and s['seconds'] <= policy['latency_seconds'] for s in samples)
record = {'lab': os.environ['DOCKYARD_LAB'], 'started_at': started, 'finished_at': datetime.now(timezone.utc).isoformat(), 'samples': samples, 'good': good, 'total': len(samples), 'ratio': good/len(samples), 'objective': policy['objective'], 'latency_seconds': policy['latency_seconds']}
Path('slo-'+name+'.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps({key:value for key,value in record.items() if key != 'samples'}))
