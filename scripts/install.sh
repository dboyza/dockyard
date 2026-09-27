#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
case "$(uname -s):$(uname -m)" in
  Darwin:arm64|Linux:aarch64|Linux:arm64|Linux:x86_64) ;;
  *) echo 'Use Apple Silicon macOS, ARM64/x86-64 Linux, or Windows through WSL 2.' >&2; exit 1 ;;
esac
if [[ "$(uname -r)" == *[Mm]icrosoft* ]]; then
  case "$PWD" in /mnt/*) echo 'Keep the checkout in the Linux filesystem, not a Windows drive mount.' >&2; exit 1 ;; esac
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
  --reinstall "dist/dockyard_learn-$(.venv/bin/python -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')-py3-none-any.whl"
./dockyard --data-dir .runtime/install-check audit
printf '\nInstalled. Run ./dockyard to open the learning workbench.\n'
