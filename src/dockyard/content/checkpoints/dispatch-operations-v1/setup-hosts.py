"""Prepare a separate guest operator client without changing the managed host client."""

from dockyard.native import current

runtime = current()
primary = "d" + runtime.lab.id[:10] + "-cp1"
result = runtime.guest(
    primary,
    [
        "sh",
        "-c",
        'mkdir -p -m 700 "$HOME/.kube"; sudo install -m 600 -o "$(id -u)" -g "$(id -g)" /etc/kubernetes/admin.conf "$HOME/.kube/operator.conf"',
    ],
)
runtime.require(result)
print("Prepared the separate guest operator client.")
