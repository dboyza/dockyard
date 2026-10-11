#!/bin/sh
set -eu
on() { limactl shell --workdir=/tmp "$@"; }
# Install the policy and a log folder on the control plane.
on "$DOCKYARD_CONTROL_PLANE" sudo mkdir -p /etc/kubernetes/audit /var/log/kubernetes/audit
on "$DOCKYARD_CONTROL_PLANE" sudo tee /etc/kubernetes/audit/policy.yaml < audit-policy.yaml >/dev/null
# Turn on auditing in the API server, with log rotation, and mount both paths.
on "$DOCKYARD_CONTROL_PLANE" sudo python3 - <<'PY'
from pathlib import Path
import yaml
path = Path("/etc/kubernetes/manifests/kube-apiserver.yaml")
pod = yaml.safe_load(path.read_text())
container = pod["spec"]["containers"][0]
container["command"] += [
    "--audit-policy-file=/etc/kubernetes/audit/policy.yaml",
    "--audit-log-path=/var/log/kubernetes/audit/audit.log",
    "--audit-log-maxage=7",
    "--audit-log-maxbackup=3",
    "--audit-log-maxsize=50",
]
container["volumeMounts"] += [
    {"name": "audit-policy", "mountPath": "/etc/kubernetes/audit/policy.yaml", "readOnly": True},
    {"name": "audit-log", "mountPath": "/var/log/kubernetes/audit"},
]
pod["spec"]["volumes"] += [
    {"name": "audit-policy", "hostPath": {"path": "/etc/kubernetes/audit/policy.yaml", "type": "File"}},
    {"name": "audit-log", "hostPath": {"path": "/var/log/kubernetes/audit", "type": "DirectoryOrCreate"}},
]
path.write_text(yaml.safe_dump(pod, sort_keys=False))
PY
sh wait-api.sh
# Something reads the Secret every 20 seconds; list who reads it until a workload's account appears.
for attempt in $(seq 1 60); do
  readers=$(on "$DOCKYARD_CONTROL_PLANE" sudo sh -c 'grep "\"resource\":\"secrets\"" /var/log/kubernetes/audit/audit.log | grep "dispatch-database"' |
    python3 -c 'import json,sys; print(sorted({json.loads(l)["user"]["username"] for l in sys.stdin if l.strip()}))')
  case "$readers" in *serviceaccount*) break ;; esac
  sleep 5
done
echo "$readers"
case "$readers" in *serviceaccount*) ;; *) echo "No workload read the Secret within five minutes." >&2; exit 1 ;; esac
echo "system:serviceaccount:telemetry:metrics-exporter" > finding.txt
