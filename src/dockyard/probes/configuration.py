"""ConfigMap/Secret delivery and authorization with an actual workload token."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from contextlib import suppress
from typing import Any

from dockyard.probes.kubernetes import (
    api_request,
    available,
    get,
    job_roundtrip,
    kubectl,
    owned_pods,
)

BANNER = "Configured through the Kubernetes API."


def delivery(namespace: str, environment: str) -> dict[str, bool]:
    result = {"config": False, "secret": False}
    try:
        deployment, pods = owned_pods("dispatch", namespace)
        response = api_request("/config", namespace=namespace)
        settings = get("configmap", "dispatch-settings", namespace)
        config = response == {"environment": environment, "banner": BANNER}
        config = config and settings["data"]["environment"] == environment
        config = config and settings["data"]["banner.txt"].strip() == BANNER
        secret = get("secret", "dispatch-database", namespace)
        credential = base64.b64decode(secret["data"]["password"]).decode()
        expected = os.environ["DOCKYARD_DB_PASSWORD"] + (
            "-preview" if namespace == "preview" else ""
        )
        secret_ok = credential == expected
        for pod in pods:
            spec = pod["spec"]
            api = next(c for c in spec["containers"] if c["name"] == "api")
            env = {item["name"]: item for item in api.get("env", [])}
            reference = env.get("DISPATCH_ENV", {}).get("valueFrom", {}).get("configMapKeyRef", {})
            config = (
                config
                and reference.get("name") == "dispatch-settings"
                and reference.get("key") == "environment"
            )
            volumes = {v["name"]: v for v in spec.get("volumes", [])}
            mounts = {m["mountPath"]: m for m in api.get("volumeMounts", [])}
            settings_mount = mounts.get("/config", {})
            settings_ref = volumes.get(settings_mount.get("name", ""), {}).get("configMap", {})
            config = (
                config
                and settings_ref.get("name") == "dispatch-settings"
                and settings_mount.get("readOnly", False)
            )
            secret_mount = mounts.get("/var/run/dispatch", {})
            secret_ref = volumes.get(secret_mount.get("name", ""), {}).get("secret", {})
            secret_ok = (
                secret_ok
                and secret_mount.get("readOnly", False)
                and secret_ref.get("secretName") == "dispatch-database"
                and "DB_PASSWORD" not in env
                and env.get("DB_PASSWORD_FILE", {}).get("value") == "/var/run/dispatch/password"
            )
            observed = kubectl(
                "exec",
                "-n",
                namespace,
                pod["metadata"]["name"],
                "-c",
                "api",
                "--",
                "python",
                "-c",
                "from pathlib import Path; import hashlib; "
                "print(hashlib.sha256(Path('/var/run/dispatch/password')"
                ".read_bytes().strip()).hexdigest())",
            )
            secret_ok = secret_ok and observed == hashlib.sha256(credential.encode()).hexdigest()
        result["config"] = bool(config and len(pods) == 2 and available(deployment, 2))
        result["secret"] = bool(
            secret_ok
            and len(pods) == 2
            and api_request("/readyz", namespace=namespace).get("ready")
        )
    except (RuntimeError, ValueError, KeyError, StopIteration):
        pass
    return result


def identity() -> bool:
    deployment, _ = owned_pods("inventory")
    if deployment["spec"]["template"]["spec"].get("serviceAccountName") != "dispatch-reader":
        return False
    script = """
import json,ssl,urllib.request,urllib.error
from pathlib import Path
root=Path('/var/run/secrets/kubernetes.io/serviceaccount')
context=ssl.create_default_context(cafile=str(root/'ca.crt'))
headers={'Authorization':'Bearer '+(root/'token').read_text().strip()}
results=[]
for path in ('/api/v1/namespaces/dispatch/pods','/api/v1/namespaces/dispatch/secrets',
             '/api/v1/namespaces/kube-system/pods'):
    request=urllib.request.Request('https://kubernetes.default.svc'+path,headers=headers)
    try:
        with urllib.request.urlopen(request,context=context,timeout=3) as response:
            body=json.load(response)
            results.append({'status':response.status,'kind':body.get('kind'),'count':len(body.get('items',[]))})
    except urllib.error.HTTPError as error:
        results.append({'status':error.code})
for verb in ('create','patch','update','delete'):
    body={'apiVersion':'authorization.k8s.io/v1','kind':'SelfSubjectAccessReview',
          'spec':{'resourceAttributes':{'namespace':'dispatch','verb':verb,'resource':'pods'}}}
    request=urllib.request.Request(
        'https://kubernetes.default.svc/apis/authorization.k8s.io/v1/selfsubjectaccessreviews',
        data=json.dumps(body).encode(),headers={**headers,'Content-Type':'application/json'})
    with urllib.request.urlopen(request,context=context,timeout=3) as response:
        results.append({'allowed':json.load(response)['status']['allowed']})
print(json.dumps(results))
"""
    try:
        observations = json.loads(
            kubectl("exec", "deployment/inventory", "-c", "client", "--", "python", "-c", script)
        )
        _, business_pods = owned_pods("dispatch")
        no_tokens = all(
            pod["spec"].get("automountServiceAccountToken") is False
            and pod["spec"].get("serviceAccountName") == "dispatch-app"
            for pod in business_pods
        )
        for pod in business_pods:
            kubectl(
                "exec",
                pod["metadata"]["name"],
                "-c",
                "api",
                "--",
                "python",
                "-c",
                "from pathlib import Path; assert not "
                "Path('/var/run/secrets/kubernetes.io/serviceaccount/token').exists()",
            )
        return bool(
            no_tokens
            and len(business_pods) == 2
            and observations[0]["status"] == 200
            and observations[0]["kind"] == "PodList"
            and observations[0]["count"] >= 2
            and observations[1]["status"] == 403
            and observations[2]["status"] == 403
            and len(observations) == 7
            and all(item["allowed"] is False for item in observations[3:])
        )
    except (RuntimeError, ValueError, KeyError, IndexError):
        return False


def configuration() -> dict[str, Any]:
    result: dict[str, Any] = delivery("dispatch", "learning")
    try:
        result["processing"] = job_roundtrip()
    except (RuntimeError, ValueError, KeyError):
        result["processing"] = False
    result["identity"] = identity()
    result["preview"] = False
    if os.environ["DOCKYARD_UNIT"] == "m09-mission":
        preview = delivery("preview", "preview")
        with suppress(RuntimeError, ValueError, KeyError):
            result["preview"] = all(preview.values()) and job_roundtrip("preview")
    return result
