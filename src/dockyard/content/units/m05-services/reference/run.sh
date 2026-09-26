#!/bin/sh
set -eu
docker compose up -d --build --wait --wait-timeout 90
