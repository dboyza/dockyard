#!/bin/sh
set -eu
# Run inside this lab's primary guest as root.
etcd_id=$(crictl ps --name '^etcd$' -q)
test -n "$etcd_id"
crictl exec "$etcd_id" etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /var/lib/etcd/dockyard-recovery.db
crictl exec "$etcd_id" etcdutl snapshot status /var/lib/etcd/dockyard-recovery.db -w json
