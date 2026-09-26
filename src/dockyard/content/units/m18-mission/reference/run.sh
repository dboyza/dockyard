#!/bin/sh
set -eu
python render.py network.yaml | kubectl apply -f -
python restore.py
python rotate.py
/bin/sh repair-image.sh
