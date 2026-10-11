#!/bin/sh
set -eu
on() { limactl shell --workdir=/tmp "$@"; }
# 5 first: record the changed replica before anything replaces it.
for pod in $(kubectl get pods -n uploads -l app=uploader -o name); do
  print=$(kubectl exec -n uploads "$pod" -- sh -c 'find /usr /etc /bin /sbin -xdev -type f ! -path /etc/hosts ! -path /etc/hostname ! -path /etc/resolv.conf -exec md5sum {} + 2>/dev/null | sort | md5sum')
  echo "$print ${pod#pod/}"
done | sort > fingerprints.txt
awk '{print $1}' fingerprints.txt | uniq -u | while read -r odd; do
  grep "^$odd" fingerprints.txt | awk '{print $NF}' > tampered-pod.txt
done
python render.py uploads.yaml | kubectl apply -f -
# 1. seccomp profile on both nodes, then both containers filtered.
for node in "$DOCKYARD_CONTROL_PLANE" "$DOCKYARD_WORKER"; do
  on "$node" sudo mkdir -p /var/lib/kubelet/seccomp/profiles
  on "$node" sudo tee /var/lib/kubelet/seccomp/profiles/no-chmod.json < profiles/no-chmod.json >/dev/null
done
python render.py processing.yaml | kubectl apply -f -
# 2. gVisor on the worker, a RuntimeClass, and the preview inside it.
on "$DOCKYARD_WORKER" sudo sh -c 'grep -q "runtimes.runsc\]" /etc/containerd/config.toml || cat >> /etc/containerd/config.toml <<EOC

[plugins."io.containerd.cri.v1.runtime".containerd.runtimes.runsc]
  runtime_type = "io.containerd.runsc.v1"
EOC
systemctl restart containerd'
kubectl wait --for=condition=Ready "node/lima-$DOCKYARD_WORKER" --timeout=120s
kubectl label node "lima-$DOCKYARD_WORKER" sandbox.dockyard.io/gvisor=true --overwrite
kubectl apply -f runtimeclass.yaml
python render.py untrusted.yaml | kubectl apply -f -
# 3. Falco with a rule for shells in containers.
cat > dockyard.yaml <<'RULE'
- rule: Shell in application container
  desc: A shell process started inside a container outside kube-system.
  condition: spawned_process and container and proc.name in (sh, bash, dash, ash) and not k8s.ns.name in (kube-system)
  output: Shell in application container (namespace=%k8s.ns.name pod=%k8s.pod.name command=%proc.cmdline)
  priority: WARNING
RULE
on "$DOCKYARD_WORKER" sudo tee /etc/falco/rules.d/dockyard.yaml < dockyard.yaml >/dev/null
on "$DOCKYARD_WORKER" sudo falco -V /etc/falco/falco_rules.yaml -V /etc/falco/rules.d/dockyard.yaml
on "$DOCKYARD_WORKER" sudo systemctl enable --now falco
# 4. Contain storefront/catalog, keeping its Pod.
echo "storefront/catalog" > finding.txt
kubectl delete rolebinding catalog-support -n dispatch
kubectl apply -f quarantine.yaml
# 6. Identities in reports.
kubectl delete rolebinding reports-default-edit -n reports
kubectl delete secret default-token-legacy -n reports
python render.py reports.yaml | kubectl apply -f -
kubectl rollout restart deployment/report-viewer -n reports
# 7. Worker footprint.
on "$DOCKYARD_WORKER" sudo systemctl disable --now report-share
on "$DOCKYARD_WORKER" sudo systemctl mask report-share
on "$DOCKYARD_WORKER" sudo rm -f /etc/sudoers.d/backup
on "$DOCKYARD_WORKER" sudo usermod --shell /usr/sbin/nologin --lock backup
# 8. WireGuard between the nodes.
kubectl patch felixconfigurations.crd.projectcalico.org default --type=merge -p '{"spec":{"wireguardEnabled":true}}'
for deployment in processing/processor processing/intake untrusted/template-preview uploads/uploader reports/report-builder reports/report-viewer; do
  kubectl rollout status "deployment/${deployment#*/}" -n "${deployment%/*}" --timeout=180s
done
for attempt in $(seq 1 60); do
  on "$DOCKYARD_WORKER" ip link show wireguard.cali >/dev/null 2>&1 && break
  sleep 2
done
