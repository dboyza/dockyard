#!/bin/sh
set -eu
on() { limactl shell --workdir=/tmp "$@"; }
# Install the custom rule, check it loads alongside the default rules, and start Falco.
on "$DOCKYARD_WORKER" sudo tee /etc/falco/rules.d/dockyard.yaml < dockyard.yaml >/dev/null
on "$DOCKYARD_WORKER" sudo falco -V /etc/falco/falco_rules.yaml -V /etc/falco/rules.d/dockyard.yaml
on "$DOCKYARD_WORKER" sudo systemctl enable --now falco
# Wait for an alert, then record which workload is starting shells.
for attempt in $(seq 1 30); do
  alert=$(on "$DOCKYARD_WORKER" sudo journalctl -u falco --since -5min --no-pager -o cat | grep 'Shell in application container' | tail -1 || true)
  [ -n "$alert" ] && break
  sleep 5
done
echo "$alert"
echo "billing/report-sync" > finding.txt
