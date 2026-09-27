#!/bin/sh
set -eu
# Run inside this lab's primary guest as root.
etcd_id=$(crictl ps --name '^etcd$' -q)
test -n "$etcd_id"
node=$(hostname)
peer=$(python3 - <<'PYTHON'
from pathlib import Path
import re
text = Path('/etc/kubernetes/manifests/etcd.yaml').read_text()
print(re.search(r'--initial-advertise-peer-urls=(https://[^\s]+)', text).group(1))
PYTHON
)
crictl exec "$etcd_id" etcdutl snapshot status /var/lib/etcd/dockyard-recovery.db -w json
crictl exec "$etcd_id" etcdutl snapshot restore /var/lib/etcd/dockyard-recovery.db \
  --data-dir=/var/lib/etcd/dockyard-restored \
  --name="$node" --initial-cluster="$node=$peer" \
  --initial-advertise-peer-urls="$peer" \
  --bump-revision=1000000000 --mark-compacted
python3 - <<'PYTHON'
from pathlib import Path
p = Path('/etc/kubernetes/manifests/etcd.yaml')
source = p.read_text()
old = 'path: /var/lib/etcd\n'
assert source.count(old) == 1
backup = Path('/var/lib/dockyard/etcd-before-restore.yaml')
backup.write_text(source)
temporary = Path('/var/lib/dockyard/etcd-restored.yaml')
temporary.write_text(source.replace(old, 'path: /var/lib/etcd/dockyard-restored\n'))
temporary.replace(p)
PYTHON
