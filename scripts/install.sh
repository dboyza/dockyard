#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ "$(uname -s)" != Darwin ] || [ "$(uname -m)" != arm64 ]; then
  echo 'Dockyard is validated for Apple Silicon macOS.' >&2
  exit 1
fi
for tool in uv node npm; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Install $tool before running this source installer." >&2
    exit 1
  fi
done
if [ -L .runtime ] || [ -L .runtime/installed ] || [ -L .venv ]; then
  echo 'An installation directory is linked elsewhere; it has been preserved.' >&2
  exit 1
fi
uv sync --locked --cache-dir .tools/uv-cache
npm --prefix frontend ci
npm --prefix frontend run build
uv build --cache-dir .tools/uv-cache
if [ ! -x .runtime/installed/bin/python ]; then
  uv venv --python 3.14 --cache-dir .tools/uv-cache .runtime/installed
fi
uv pip install --cache-dir .tools/uv-cache --python .runtime/installed/bin/python \
  --reinstall dist/dockyard_learn-0.1.0-py3-none-any.whl
./dockyard --data-dir .runtime/install-check audit
printf '\nInstalled. Run ./dockyard to open the learning workbench.\n'
