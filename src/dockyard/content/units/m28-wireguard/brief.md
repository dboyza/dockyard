## Encrypt Pod traffic between nodes

Requests from the frontend on the control plane to Dispatch on the worker cross the node network unencrypted.

1. Confirm the worker has no `wireguard.cali` interface.
2. Enable WireGuard in Calico's `default` FelixConfiguration.
3. Confirm both nodes publish a WireGuard public key and have a `wireguard.cali` interface.
4. Confirm cross-node traffic now passes through the tunnel, and choose **Check work**.

Dispatch must keep processing jobs.
In your notes, compare node-to-node WireGuard encryption with a service mesh's mutual TLS: what does each protect, and what does each cost?
