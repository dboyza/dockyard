"""Wait for available replicas and fresh measurements, not just an HPA declaration."""
import json
import subprocess
import time


def query(*args):
    return json.loads(subprocess.run(['kubectl', *args], capture_output=True, text=True, check=True).stdout)


def observe():
    hpa = query('get', 'hpa', 'dispatch', '-o', 'json')
    status = hpa.get('status', {})
    deployment = query('get', 'deployment', 'dispatch', '-o', 'json')
    pods = query('get', 'pods', '-l', 'app=dispatch,track=stable', '-o', 'json')['items']
    active = {p['metadata']['name'] for p in pods if not p['metadata'].get('deletionTimestamp')}
    metrics = query('get', '--raw', '/apis/metrics.k8s.io/v1beta1/namespaces/dispatch/pods')
    measured = {m['metadata']['name'] for m in metrics['items']}
    return (status.get('currentReplicas') == status.get('desiredReplicas') == 4
            and deployment.get('status', {}).get('availableReplicas') == 4
            and len(active) == 4 and active <= measured)


# Metrics Server can take a minute to serve again after a lab is resumed, so an
# unavailable metrics API means "not yet", not failure.
end = time.monotonic() + 300
waiting_for_metrics = False
while time.monotonic() < end:
    try:
        if observe():
            print('Four API replicas are available and each has a current Metrics Server sample.')
            break
    except subprocess.CalledProcessError:
        if not waiting_for_metrics:
            print('Waiting for the metrics API to answer...')
            waiting_for_metrics = True
    time.sleep(2)
else:
    raise SystemExit('Scale-up did not converge. Inspect HPA conditions, requests, load, and current Pod metrics.')
