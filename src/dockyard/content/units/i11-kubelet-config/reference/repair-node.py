from dockyard.native import current
r = current()
worker = "d" + r.lab.id[:10] + "-worker"
r.require(r.guest(worker, ["sudo", "python3", "-c", "from pathlib import Path; p=Path('/var/lib/kubelet/config.yaml'); s=p.read_text(); assert s.count('shutdownGracePeriod: invalid-duration') == 1; p.write_text(s.replace('shutdownGracePeriod: invalid-duration','shutdownGracePeriod: 0s'))"]))
r.require(r.guest(worker, ["sudo", "systemctl", "restart", "kubelet"]))
