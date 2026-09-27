#!/bin/sh
set -eu
sh run.sh
python -m dockyard.fixtures.exam ckad-a
