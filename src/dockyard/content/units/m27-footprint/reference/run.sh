#!/bin/sh
set -eu
on() { limactl shell --workdir=/tmp "$@"; }
# Survey what runs and listens on the worker.
on "$DOCKYARD_WORKER" systemctl list-units --type=service --state=running --no-pager
on "$DOCKYARD_WORKER" sudo ss -ltnp
# The report share is not needed: stop it, keep it from starting again, and close its port.
on "$DOCKYARD_WORKER" sudo systemctl disable --now report-share
on "$DOCKYARD_WORKER" sudo systemctl mask report-share
# The backup account is unused: remove its sudo rule and its login shell.
on "$DOCKYARD_WORKER" sudo rm -f /etc/sudoers.d/backup
on "$DOCKYARD_WORKER" sudo usermod --shell /usr/sbin/nologin --lock backup
on "$DOCKYARD_WORKER" sudo ss -ltnp
