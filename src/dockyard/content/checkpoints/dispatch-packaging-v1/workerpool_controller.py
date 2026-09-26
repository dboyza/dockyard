"""A supplied, namespaced WorkerPool controller with explicit ownership checks."""

import json
import os
import signal
import ssl
import threading
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path('/var/run/secrets/kubernetes.io/serviceaccount')
NAMESPACE = ROOT.joinpath('namespace').read_text().strip()
CONTEXT = ssl.create_default_context(cafile=str(ROOT / 'ca.crt'))
STOP = threading.Event()
API = 'https://kubernetes.default.svc'
POOLS = f'/apis/learning.dockyard.local/v1alpha1/namespaces/{NAMESPACE}/workerpools'
DEPLOYMENTS = f'/apis/apps/v1/namespaces/{NAMESPACE}/deployments'


def request(path, method='GET', body=None):
    headers = {'Authorization': 'Bearer ' + (ROOT / 'token').read_text().strip()}
    if body is not None:
        headers['Content-Type'] = 'application/merge-patch+json' if method == 'PATCH' else 'application/json'
    req = urllib.request.Request(API + path, method=method, headers=headers,
                                 data=json.dumps(body).encode() if body is not None else None)
    with urllib.request.urlopen(req, context=CONTEXT, timeout=10) as response:
        return json.load(response)


def contains(actual, desired):
    if isinstance(desired, dict):
        return isinstance(actual, dict) and all(key in actual and contains(actual[key], value)
                                               for key, value in desired.items())
    if isinstance(desired, list):
        return isinstance(actual, list) and len(actual) == len(desired) and all(
            contains(left, right) for left, right in zip(actual, desired))
    return actual == desired


def desired(pool):
    metadata = pool['metadata']
    labels = {'app': 'managed-worker', 'learning.dockyard.local/pool': metadata['name']}
    return {
        'apiVersion': 'apps/v1', 'kind': 'Deployment',
        'metadata': {
            'name': metadata['name'] + '-workers', 'namespace': NAMESPACE, 'labels': labels,
            'ownerReferences': [{'apiVersion': pool['apiVersion'], 'kind': 'WorkerPool',
                                 'name': metadata['name'], 'uid': metadata['uid'],
                                 'controller': True}],
        },
        'spec': {
            'replicas': pool['spec']['replicas'], 'selector': {'matchLabels': labels},
            'template': {'metadata': {'labels': labels}, 'spec': {
                'enableServiceLinks': False, 'serviceAccountName': 'dispatch-app',
                'automountServiceAccountToken': False,
                'containers': [{
                    'name': 'worker', 'image': os.environ['APP_IMAGE'], 'imagePullPolicy': 'Never',
                    'command': ['python', 'worker.py'],
                    'resources': {'requests': {'cpu': '25m', 'memory': '32Mi'},
                                  'limits': {'cpu': '300m', 'memory': '192Mi'}},
                    'env': [{'name': 'DB_HOST', 'value': 'db'},
                            {'name': 'REDIS_URL', 'value': 'redis://queue:6379/0'},
                            {'name': 'DB_PASSWORD_FILE', 'value': '/var/run/dispatch/password'}],
                    'volumeMounts': [{'name': 'credential', 'mountPath': '/var/run/dispatch', 'readOnly': True}],
                }],
                'volumes': [{'name': 'credential', 'secret': {'secretName': 'dispatch-database'}}],
            }},
        },
    }


def reconcile(pool):
    target = desired(pool)
    path = DEPLOYMENTS + '/' + target['metadata']['name']
    try:
        current = request(path)
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        current = request(DEPLOYMENTS, 'POST', target)
        print(json.dumps({'event': 'created', 'pool': pool['metadata']['name']}), flush=True)
    owners = current['metadata'].get('ownerReferences', [])
    if not any(owner['uid'] == pool['metadata']['uid'] and owner.get('controller') for owner in owners):
        reason = 'OwnershipConflict'
        ready = False
    else:
        if not contains(current['spec'], target['spec']):
            current = request(path, 'PATCH', {'spec': target['spec']})
            print(json.dumps({'event': 'reconciled', 'pool': pool['metadata']['name'],
                              'replicas': pool['spec']['replicas']}), flush=True)
        status = current.get('status', {})
        ready = status.get('availableReplicas', 0) == pool['spec']['replicas'] and (
            status.get('observedGeneration') == current['metadata']['generation'])
        reason = 'Available' if ready else 'Progressing'
    observed = {
        'observedGeneration': pool['metadata']['generation'],
        'deployment': target['metadata']['name'],
        'conditions': [{'type': 'Ready', 'status': 'True' if ready else 'False',
                        'reason': reason, 'observedGeneration': pool['metadata']['generation']}],
    }
    if pool.get('status') != observed:
        request(POOLS + '/' + pool['metadata']['name'] + '/status', 'PATCH', {'status': observed})


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: STOP.set())
    while not STOP.is_set():
        try:
            for pool in request(POOLS)['items']:
                reconcile(pool)
        except (urllib.error.URLError, OSError, ValueError, KeyError) as error:
            print(json.dumps({'event': 'retry', 'type': type(error).__name__,
                              'status': getattr(error, 'code', None)}), flush=True)
        STOP.wait(2)
