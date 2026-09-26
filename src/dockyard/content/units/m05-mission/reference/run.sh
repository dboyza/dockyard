#!/bin/sh
set -eu
docker compose up -d --build --scale worker=2 --wait --wait-timeout 90
