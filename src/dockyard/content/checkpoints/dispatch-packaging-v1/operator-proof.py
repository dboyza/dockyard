"""Record a real perturbation and subsequent controller repair of its owned Deployment."""
import json
import os
import subprocess
import time
from pathlib import Path


def command(*args):
    return subprocess.run(['kubectl', *args], text=True, capture_output=True, check=True).stdout


pool = json.loads(command('get', 'workerpool', 'dispatch', '-o', 'json'))
before = json.loads(command('get', 'deployment', 'dispatch-workers', '-o', 'json'))
if before['spec']['replicas'] != 2 or pool['spec']['replicas'] != 2:
    raise SystemExit('Start with the WorkerPool and its managed Deployment requesting two replicas.')
started = time.monotonic()
# Capture the API response from the exact mutation, before the controller can overwrite it.
perturbed = json.loads(command('patch', 'deployment', 'dispatch-workers', '--type=merge', '-p', '{"spec":{"replicas":0}}', '-o', 'json'))
while time.monotonic() - started < 120:
    deployment = json.loads(command('get', 'deployment', 'dispatch-workers', '-o', 'json'))
    status = deployment.get('status', {})
    if (deployment['spec']['replicas'] == 2 and status.get('availableReplicas') == 2
            and status.get('observedGeneration') == deployment['metadata']['generation']):
        record = {
            'lab': os.environ['DOCKYARD_LAB'], 'pool_uid': pool['metadata']['uid'],
            'deployment_uid': deployment['metadata']['uid'],
            'before_replicas': before['spec']['replicas'], 'perturbed_replicas': perturbed['spec']['replicas'],
            'after_replicas': deployment['spec']['replicas'],
            'before_generation': before['metadata']['generation'],
            'perturbed_generation': perturbed['metadata']['generation'],
            'after_generation': deployment['metadata']['generation'],
            'elapsed_seconds': round(time.monotonic() - started, 3),
        }
        Path('operator-evidence.json').write_text(json.dumps(record, indent=2) + '\n')
        print(json.dumps(record))
        break
    time.sleep(.5)
else:
    raise SystemExit('The controller did not restore two available workers within the rehearsal deadline.')
