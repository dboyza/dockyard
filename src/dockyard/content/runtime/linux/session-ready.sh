#!/usr/bin/env bash
# This is infrastructure recovery, not a repair of any taught Kubernetes component.
set -euo pipefail
test "$(hostname)" = "${DOCKYARD_GUEST:?Expected guest hostname is required}"
test "$(id -u)" = 0
healthy() {
  timeout 3 busctl --system --timeout=2s call \
    org.freedesktop.login1 /org/freedesktop/login1 org.freedesktop.DBus.Peer Ping >/dev/null 2>&1
}
if ! healthy; then
  echo 'Recovering an unresponsive guest login manager.' >&2
  if systemctl is-active --quiet systemd-logind; then
    systemctl kill --kill-whom=main --signal=KILL systemd-logind
  fi
  timeout 10 systemctl start systemd-logind
fi
for attempt in 1 2 3 4 5; do
  if healthy; then
    exit 0
  fi
  sleep 0.2
done
echo 'The guest login manager remains unavailable after bounded recovery.' >&2
exit 1
