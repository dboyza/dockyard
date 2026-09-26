#!/bin/sh
set -eu
docker compose up -d --scale worker=2 --wait --wait-timeout 90
docker compose --profile tools run --rm inspect
