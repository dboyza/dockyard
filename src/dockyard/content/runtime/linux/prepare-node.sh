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
# Every local .deb is pinned to an official repository artifact and hash-verified on the host.
# dpkg installs this explicit bundle only and has no repository download mechanism.
dpkg --install "${DOCKYARD_PACKAGE_DIR:?Private package directory required}"/*.deb >&2
mkdir -p /etc/containerd /etc/apt/keyrings
containerd config default >/etc/containerd/config.toml
sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
systemctl enable --now containerd
systemctl restart containerd
cat >/etc/crictl.yaml <<'EOF'
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
timeout: 10
debug: false
EOF
apt-mark hold kubelet kubeadm kubectl
systemctl enable kubelet
kubeadm version -o short
