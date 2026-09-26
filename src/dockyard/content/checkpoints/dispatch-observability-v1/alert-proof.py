"""Exercise a real latency alert through a controlled failure and recovery."""
import hashlib
import json
import os
import subprocess
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path


def command(*args):
    return subprocess.run(['kubectl', *args], capture_output=True, text=True, check=True).stdout


def request(path):
    script = 'import urllib.request;print(urllib.request.urlopen('+repr('http://prometheus:9090'+path)+',timeout=5).read().decode())'
    return json.loads(command('exec', 'deployment/dispatch', '-c', 'api', '--', 'python', '-c', script))


def delay(value):
    command('patch', 'configmap', 'dispatch-settings', '--type=merge', '-p', json.dumps({'data': {'delay_ms': str(value)}}))
    command('rollout', 'restart', 'deployment/dispatch')
    command('rollout', 'status', 'deployment/dispatch', '--timeout=120s')


def wait_for(firing):
    end = time.monotonic() + 150
    while time.monotonic() < end:
        try:
            data = request('/api/v1/alerts')['data']['alerts']
            active = [a for a in data if a['labels'].get('alertname') == 'DispatchLatencyBudgetBurn' and a['state'] == 'firing']
            if bool(active) == firing:
                query = 'sum(rate(dispatch_http_request_duration_seconds_bucket{le="0.25"}[1m])) / sum(rate(dispatch_http_request_duration_seconds_count[1m]))'
                measured = request('/api/v1/query?' + urllib.parse.urlencode({'query':query}))['data']['result']
                ratio = float(measured[0]['value'][1]) if measured else None
                if ratio is not None and ((firing and ratio < .9) or (not firing and ratio >= .95)):
                    return {'at':datetime.now(timezone.utc).isoformat(), 'firing':bool(active), 'good_ratio':ratio}
        except (subprocess.CalledProcessError, KeyError, ValueError, IndexError):
            pass
        time.sleep(2)
    raise RuntimeError('The latency alert did not reach the expected measured state. Inspect rules and scrape targets.')


started = datetime.now(timezone.utc).isoformat()
try:
    delay(600)
    failure = wait_for(True)
finally:
    delay(20)
recovery = wait_for(False)
record = {'lab':os.environ['DOCKYARD_LAB'],'started_at':started,'failure':failure,'recovery':recovery,'rules_sha256':hashlib.sha256(Path('rules.yaml').read_bytes()).hexdigest(),'dashboard_sha256':hashlib.sha256(Path('dashboard.json').read_bytes()).hexdigest()}
Path('alert-evidence.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
