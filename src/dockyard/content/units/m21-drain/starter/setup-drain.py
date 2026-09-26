import json

from dockyard.native import current

r = current()
patch = {
    "spec": {
        "template": {
            "spec": {
                "nodeSelector": None,
                "affinity": {
                    "nodeAffinity": {
                        "requiredDuringSchedulingIgnoredDuringExecution": {
                            "nodeSelectorTerms": [
                                {
                                    "matchExpressions": [
                                        {
                                            "key": "node-role.kubernetes.io/control-plane",
                                            "operator": "DoesNotExist",
                                        }
                                    ]
                                }
                            ]
                        }
                    },
                    "podAntiAffinity": {
                        "preferredDuringSchedulingIgnoredDuringExecution": [
                            {
                                "weight": 100,
                                "podAffinityTerm": {
                                    "labelSelector": {
                                        "matchLabels": {
                                            "app": "dispatch",
                                            "track": "stable",
                                        }
                                    },
                                    "topologyKey": "kubernetes.io/hostname",
                                },
                            }
                        ]
                    },
                },
            }
        }
    }
}
r.require(
    r.kubectl(
        ["patch", "deployment", "dispatch", "--type=merge", "-p", json.dumps(patch)]
    )
)
r.require(
    r.kubectl(
        ["rollout", "status", "deployment/dispatch", "--timeout=180s"], timeout=190
    )
)
pdb = {
    "apiVersion": "policy/v1",
    "kind": "PodDisruptionBudget",
    "metadata": {"name": "dispatch-maintenance", "namespace": "dispatch"},
    "spec": {
        "minAvailable": 2,
        "selector": {"matchLabels": {"app": "dispatch", "track": "stable"}},
    },
}
r.require(r.kubectl(["apply", "-f", "-"], payload=json.dumps(pdb)))
result = r.kubectl(["get", "pods", "-l", "app=dispatch,track=stable", "-o", "json"])
r.require(result)
expected = {"lima-d" + r.lab.id[:10] + "-worker", "lima-d" + r.lab.id[:10] + "-worker2"}
actual = {
    p["spec"].get("nodeName")
    for p in json.loads(result.stdout)["items"]
    if not p["metadata"].get("deletionTimestamp")
}
if actual != expected:
    raise RuntimeError(
        "Maintenance fixture did not spread API replicas across both workers."
    )
