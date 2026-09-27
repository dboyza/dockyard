# Debrief: Reconnect node supervision through systemd

An active systemd unit shows that a process is running, while fresh node leases show that the kubelet is communicating with the API.
Node readiness and a new completed application job then test different parts of the restored supervision chain.

## Explain your result

Explain why an old Ready condition could be misleading immediately after a restart and which timestamp establishes fresh communication.

## Transfer beyond this lab

After changing node configuration, inspect the service journal and validate both node communication and workload behavior before declaring recovery.
