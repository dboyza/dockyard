## Ready nodes, but lost packets

Two nodes can both show Ready while traffic between their Pods is silently dropped.
That is because node health and Pod traffic travel differently:

- The kubelet reports to the API server over the **node network**, `192.168.104.0/24`.
- Pod-to-Pod traffic between nodes is wrapped by Calico in **VXLAN** packets: ordinary UDP packets on port **4789** between the node addresses, carrying the Pod packet inside. Pod addresses come from `10.244.0.0/16`.

Block UDP 4789 and the nodes stay Ready, but Pods on different nodes can no longer reach each other.

```figure
two-paths
```

## This lab

Dispatch’s API and database run on the worker.
The trusted frontend client runs on the control plane, so its requests must cross between the machines.
The dashboard you open in the browser connects straight to the worker, so it can look fine while the frontend’s path is broken.

Someone has added a firewall rule on the control-plane VM that drops UDP port 4789.
It is an **iptables** rule in the `raw` table’s `PREROUTING` chain, the very first place incoming packets are checked, and it carries the comment `dockyard-$DOCKYARD_LAB-vxlan`.

## Worked example: find the path, then the rule

```sh
kubectl get nodes -o wide
kubectl get pods -n frontend -o wide
kubectl get pods -l app=dispatch -o wide
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" ip -d link show vxlan.calico
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo iptables -t raw -nvL PREROUTING --line-numbers
```

- The first three show which node each piece runs on and the API Pod’s IP address.
- `ip -d link show vxlan.calico` shows Calico’s VXLAN interface exists; it existing is not proof traffic flows.
- `iptables -t raw -nvL PREROUTING --line-numbers` lists the rules with packet counters (`-v`) and line numbers. Try a cross-node request and run it again: a counter that rises on a DROP rule is your evidence.

Testing at different layers tells you different things:

- A request straight to the API **Pod IP** tests packet delivery alone, without DNS or Services.
- A request to the **Service name** adds DNS and Service routing back in.
- `/healthz` shows the process answers; `/readyz` or a real job also tests its dependencies.

```figure
testing-layers
```

## Remove only that rule

Delete exactly the rule you found, either by its line number from a fresh listing or by repeating its full match with `-D`:

```sh
sudo iptables -t raw -D PREROUTING -p udp --dport 4789 -m comment --comment "dockyard-$DOCKYARD_LAB-vxlan" -j DROP
```

Never flush the whole firewall with `iptables -F`: Calico and kube-proxy rely on many other rules in the same tables.

## Prove it works

Check work sends a request from the frontend to an API Pod IP on the worker.
It creates a fresh Service and checks its DNS name and ClusterIP.
It also runs a real job, and confirms the original data is still there.
