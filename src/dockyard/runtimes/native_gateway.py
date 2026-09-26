"""Explicit guest listener connecting the loopback browser forward to a real NodePort."""

from __future__ import annotations

import threading

from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.runtimes.linux import LinuxRuntime


def prepare(runtime: LinuxRuntime, cancel: threading.Event) -> None:
    worker = "d" + runtime.lab.id[:10] + "-worker"
    if worker not in {entry["name"] for entry in runtime.discover()}:
        raise RuntimeErrorBase("The application gateway requires this lab's recorded worker.")
    target = f"TCP4:lima-{worker}.internal:30080"
    unit = f"""[Unit]
Description=Dockyard private browser connection to the owned Kubernetes NodePort
After=network-online.target
Wants=network-online.target
[Service]
DynamicUser=yes
ExecStart=/usr/bin/socat TCP4-LISTEN:18080,bind=0.0.0.0,reuseaddr,fork {target}
Restart=on-failure
RestartSec=1
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
RestrictAddressFamilies=AF_INET AF_INET6
TasksMax=64
MemoryMax=64M
TimeoutStopSec=5
[Install]
WantedBy=multi-user.target
"""
    runtime.require(
        runtime.guest(
            worker,
            ["sudo", "tee", "/etc/systemd/system/dockyard-browser.service"],
            input_text=unit,
            cancel=cancel,
        )
    )
    runtime.require(runtime.guest(worker, ["sudo", "systemctl", "daemon-reload"], cancel=cancel))
    runtime.require(
        runtime.guest(
            worker, ["sudo", "systemctl", "enable", "--now", "dockyard-browser"], cancel=cancel
        )
    )
    runtime.require(
        runtime.guest(worker, ["sudo", "systemctl", "restart", "dockyard-browser"], cancel=cancel)
    )
