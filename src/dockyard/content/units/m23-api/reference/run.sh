#!/bin/sh
set -eu
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo python3 - <<'PYTHON'
from pathlib import Path
p = Path('/etc/kubernetes/manifests/kube-apiserver.yaml')
s = p.read_text()
old = '--etcd-servers=https://127.0.0.1:2399'
assert s.count(old) == 1
t = Path('/var/lib/dockyard/apiserver-repaired.yaml')
t.write_text(s.replace(old, '--etcd-servers=https://127.0.0.1:2379'))
t.replace(p)
PYTHON
python wait-control-plane.py
kubectl get nodes
