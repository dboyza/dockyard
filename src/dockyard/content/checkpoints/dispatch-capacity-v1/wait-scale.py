"""Wait for available replicas and fresh measurements, not just an HPA declaration."""
import json
import subprocess
import time


def query(*args):
    return json.loads(subprocess.run(['kubectl', *args], capture_output=True, text=True, check=True).stdout)


end = time.monotonic() + 180
while time.monotonic() < end:
    hpa = query('get', 'hpa', 'dispatch', '-o', 'json')
    status = hpa.get('status', {})
    deployment = query('get', 'deployment', 'dispatch', '-o', 'json')
    pods = query('get', 'pods', '-l', 'app=dispatch,track=stable', '-o', 'json')['items']
    active = {p['metadata']['name'] for p in pods if not p['metadata'].get('deletionTimestamp')}
    metrics = query('get', '--raw', '/apis/metrics.k8s.io/v1beta1/namespaces/dispatch/pods')
    measured = {m['metadata']['name'] for m in metrics['items']}
    if (status.get('currentReplicas') == status.get('desiredReplicas') == 4
            and deployment.get('status', {}).get('availableReplicas') == 4
            and len(active) == 4 and active <= measured):
        print('Four API replicas are available and each has a current Metrics Server sample.')
        break
    time.sleep(2)
else:
    raise SystemExit('Scale-up did not converge. Inspect HPA conditions, requests, load, and current Pod metrics.')
