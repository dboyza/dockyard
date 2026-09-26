#!/bin/sh
set -eu
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo iptables -t raw -D PREROUTING -p udp --dport 4789 -m comment --comment "dockyard-$DOCKYARD_LAB-vxlan" -j DROP
