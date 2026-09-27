import os, subprocess

base = [
    "limactl",
    "shell",
    "--workdir=/tmp",
    os.environ["DOCKYARD_CONTROL_PLANE"],
    "sudo",
    "crictl",
]
container = subprocess.check_output(base + ["ps", "--name", "^etcd$", "-q"], text=True).strip()
subprocess.run(
    base
    + [
        "exec",
        container,
        "etcdctl",
        "--endpoints=https://127.0.0.1:2379",
        "--cacert=/etc/kubernetes/pki/etcd/ca.crt",
        "--cert=/etc/kubernetes/pki/etcd/server.crt",
        "--key=/etc/kubernetes/pki/etcd/server.key",
        "snapshot",
        "save",
        "/var/lib/etcd/operations-a.db",
    ],
    check=True,
)
subprocess.run(
    base
    + [
        "exec",
        container,
        "etcdutl",
        "snapshot",
        "status",
        "/var/lib/etcd/operations-a.db",
        "-w",
        "json",
    ],
    check=True,
)
