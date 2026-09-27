#!/bin/sh
set -eu
kubectl patch service dispatch --type=json -p '[{"op":"remove","path":"/spec/selector/release-channel"}]'
