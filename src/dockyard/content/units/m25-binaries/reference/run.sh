#!/bin/sh
set -eu
on() { limactl shell --workdir=/tmp "$@"; }
for name in kubeadm kubelet kubectl; do
  # sha512sum -c reads "<checksum>  <file>" lines and reports OK or FAILED for each.
  if echo "$(cat "release-checksums/$name.sha512")  /opt/dockyard/staged/$name" |
    on "$DOCKYARD_CONTROL_PLANE" sha512sum -c -; then
    echo "$name matches the official release"
  else
    on "$DOCKYARD_CONTROL_PLANE" sudo rm -f "/opt/dockyard/staged/$name"
    echo "$name did not match and was removed"
  fi
done
on "$DOCKYARD_CONTROL_PLANE" ls -l /opt/dockyard/staged
