#!/bin/sh
set -eu
sh run.sh
python -m dockyard.fixtures.registry_incident
