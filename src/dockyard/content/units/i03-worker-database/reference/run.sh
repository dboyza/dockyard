#!/bin/sh
set -eu
docker compose up -d --scale worker=2 --wait
