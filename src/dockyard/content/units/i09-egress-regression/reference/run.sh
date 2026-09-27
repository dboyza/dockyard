#!/bin/sh
set -eu
kubectl patch networkpolicy allow-dns --type=json -p '[{"op":"replace","path":"/spec/egress/0/ports","value":[{"protocol":"UDP","port":53},{"protocol":"TCP","port":53}]}]'
kubectl patch networkpolicy allow-worker-dependencies --type=json -p '[{"op":"replace","path":"/spec/egress/1/ports/0/port","value":6379}]'
