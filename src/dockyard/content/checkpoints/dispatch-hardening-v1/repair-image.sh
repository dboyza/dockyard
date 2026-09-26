#!/bin/sh
set -eu
python build.py
for name in dispatch worker; do
  kubectl rollout restart deployment/$name
  kubectl rollout status deployment/$name --timeout=150s
done
python scan.py after
