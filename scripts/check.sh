#!/bin/bash
# Run every fast check: lint, types, formatting, unit tests, the structural audit,
# and dependency advisory scans. Real-runtime suites are listed in docs/maintenance.md.
set -euo pipefail
cd "$(dirname "$0")/.."
step() { printf '\n== %s\n' "$1"; }

step "Python lint, format, and types"
.venv/bin/ruff check src tests scripts
.venv/bin/ruff format --check src tests scripts
.venv/bin/mypy src/dockyard

step "Python tests"
.venv/bin/pytest -q -m 'not integration'

step "Frontend lint, format, types, and tests"
npm --prefix frontend run -s lint
npm --prefix frontend run -s format:check
npm --prefix frontend run -s check
npm --prefix frontend run -s test

step "Structural curriculum audit"
audit_profile="$(mktemp -d)"
trap 'rm -rf "$audit_profile"' EXIT
.venv/bin/python -m dockyard --data-dir "$audit_profile" audit

step "Dependency advisories"
requirements="$audit_profile/requirements.txt"
NO_COLOR=1 uv export --quiet --format requirements-txt --no-header --no-emit-project \
  --no-annotate --cache-dir .tools/uv-cache > "$requirements"
NO_COLOR=1 uvx --quiet --cache-dir .tools/uv-cache pip-audit --progress-spinner off \
  --disable-pip --require-hashes -r "$requirements"
npm --prefix frontend audit --audit-level=low

printf '\nAll fast checks passed.\n'
