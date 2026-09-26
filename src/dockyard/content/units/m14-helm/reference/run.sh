#!/bin/sh
set -eu
helm rollback dispatch 1 -n staging --wait --timeout 120s
