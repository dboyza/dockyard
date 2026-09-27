import json, os, subprocess
import yaml


def k(*args, payload=None):
    subprocess.run(["kubectl", *args], input=payload, text=True, check=True)


toleration = {
    "key": "dockyard.io/batch",
    "operator": "Equal",
    "value": "true",
    "effect": "NoSchedule",
}
k(
    "patch",
    "statefulset",
    "db",
    "--type=merge",
    "-p",
    json.dumps(
        {
            "spec": {
                "template": {
                    "spec": {
                        "nodeSelector": {
                            "kubernetes.io/hostname": "lima-" + os.environ["DOCKYARD_WORKER"]
                        },
                        "tolerations": [toleration],
                    }
                }
            }
        }
    ),
)
k("delete", "pod", "db-0", "--wait=true", "--timeout=60s")
k(
    "patch",
    "deployment",
    "batch-audit",
    "--type=merge",
    "-p",
    json.dumps(
        {
            "spec": {
                "template": {
                    "spec": {
                        "nodeSelector": {"dockyard.io/pool": "batch"},
                        "tolerations": [toleration],
                    }
                }
            }
        }
    ),
)
role = {
    "apiVersion": "rbac.authorization.k8s.io/v1",
    "kind": "Role",
    "metadata": {"name": "incident-observer", "namespace": "dispatch"},
    "rules": [
        {"apiGroups": [""], "resources": ["pods"], "verbs": ["get", "list", "watch"]},
        {"apiGroups": [""], "resources": ["pods/log"], "verbs": ["get"]},
    ],
}
binding = {
    "apiVersion": "rbac.authorization.k8s.io/v1",
    "kind": "RoleBinding",
    "metadata": {"name": "incident-observer", "namespace": "dispatch"},
    "subjects": [{"kind": "ServiceAccount", "name": "incident-observer", "namespace": "dispatch"}],
    "roleRef": {
        "apiGroup": "rbac.authorization.k8s.io",
        "kind": "Role",
        "name": "incident-observer",
    },
}
ds = {
    "apiVersion": "apps/v1",
    "kind": "DaemonSet",
    "metadata": {"name": "node-observer", "namespace": "dispatch"},
    "spec": {
        "selector": {"matchLabels": {"app": "node-observer"}},
        "template": {
            "metadata": {"labels": {"app": "node-observer"}},
            "spec": {
                "securityContext": {
                    "runAsNonRoot": True,
                    "seccompProfile": {"type": "RuntimeDefault"},
                },
                "tolerations": [{"operator": "Exists"}],
                "containers": [
                    {
                        "name": "observer",
                        "securityContext": {
                            "allowPrivilegeEscalation": False,
                            "capabilities": {"drop": ["ALL"]},
                        },
                        "image": os.environ["DOCKYARD_IMAGE"],
                        "imagePullPolicy": "Never",
                        "command": ["python", "-c", "import time; time.sleep(86400)"],
                        "resources": {
                            "requests": {"cpu": "10m", "memory": "16Mi"},
                            "limits": {"cpu": "100m", "memory": "64Mi"},
                        },
                    }
                ],
            },
        },
    },
}
k("apply", "-f", "-", payload=yaml.safe_dump_all([role, binding, ds]))
