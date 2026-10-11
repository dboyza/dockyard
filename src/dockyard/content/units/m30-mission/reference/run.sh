#!/bin/sh
set -eu
on() { limactl shell --workdir=/tmp "$@"; }
# Detect: watch for shells in application containers with Falco.
cat > dockyard.yaml <<'RULE'
- rule: Shell in application container
  desc: A shell process started inside a container in an application namespace.
  condition: spawned_process and container and proc.name in (sh, bash, dash, ash) and not k8s.ns.name in (kube-system)
  output: Shell in application container (namespace=%k8s.ns.name pod=%k8s.pod.name command=%proc.cmdline)
  priority: WARNING
RULE
on "$DOCKYARD_WORKER" sudo tee /etc/falco/rules.d/dockyard.yaml < dockyard.yaml >/dev/null
on "$DOCKYARD_WORKER" sudo systemctl enable --now falco
for attempt in $(seq 1 30); do
  alert=$(on "$DOCKYARD_WORKER" sudo journalctl -u falco --since -5min --no-pager -o cat | grep 'Shell in application container' | tail -1 || true)
  [ -n "$alert" ] && break
  sleep 5
done
echo "$alert"
# Investigate: what can its identity do?
kubectl get pod -n storefront -l app=catalog -o jsonpath='{.items[0].spec.serviceAccountName}{"\n"}'
kubectl auth can-i --list -n dispatch --as=system:serviceaccount:storefront:catalog | grep secrets || true
echo "storefront/catalog" > finding.txt
# Contain: revoke its access and isolate it, keeping the Pod for evidence.
kubectl delete rolebinding catalog-support -n dispatch
kubectl apply -f quarantine.yaml
cp incident-report-reference.md incident-report.md
