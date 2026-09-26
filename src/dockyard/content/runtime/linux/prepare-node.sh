#!/usr/bin/env bash
# Run only inside the exact app-owned Linux guest supplied by the runtime.
set -euo pipefail
test "$(hostname)" = "${DOCKYARD_GUEST:?Expected guest hostname is required}"
test "$(id -u)" = 0
export DEBIAN_FRONTEND=noninteractive
swapoff -a
modprobe overlay
modprobe br_netfilter
cat >/etc/modules-load.d/dockyard-kubernetes.conf <<'EOF'
overlay
br_netfilter
EOF
cat >/etc/sysctl.d/90-dockyard-kubernetes.conf <<'EOF'
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
EOF
sysctl --system >/dev/null
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg containerd conntrack socat iptables iproute2 jq haproxy
mkdir -p /etc/containerd /etc/apt/keyrings
containerd config default >/etc/containerd/config.toml
sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
systemctl enable --now containerd
systemctl restart containerd
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.35/deb/Release.key -o /tmp/dockyard-kubernetes-release.key
gpg --dearmor --yes -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg /tmp/dockyard-kubernetes-release.key
printf '%s\n' 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.35/deb/ /' >/etc/apt/sources.list.d/kubernetes.list
apt-get update -qq
apt-get install -y -qq kubelet=1.35.8-1.1 kubeadm=1.35.8-1.1 kubectl=1.35.8-1.1
apt-mark hold kubelet kubeadm kubectl
systemctl enable kubelet
kubeadm version -o short
