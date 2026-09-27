import base64
import json
import os
import subprocess
from pathlib import Path
registry = Path("registry.txt").read_text().strip()
auth = base64.b64encode(("learner:" + os.environ["DOCKYARD_REGISTRY_PASSWORD"]).encode()).decode()
config = {"auths": {registry: {"auth": auth}}}
secret = {"apiVersion": "v1", "kind": "Secret", "metadata": {"name": "registry-pull", "namespace": "dispatch"}, "type": "kubernetes.io/dockerconfigjson", "stringData": {".dockerconfigjson": json.dumps(config)}}
subprocess.run(["kubectl", "apply", "-f", "-"], input=json.dumps(secret), text=True, check=True)
