## Deciding which nodes a Pod may run on

By default the scheduler can put a Pod on any node with room.
Often you want more control: keep an application on dedicated machines, keep other workloads off them, and spread copies apart.
Kubernetes gives you separate tools for each of these, and it matters which one does what.

## Labels and node selection: where a Pod wants to go

Nodes have labels, just like Pods.
The simplest way to require a label is `nodeSelector`:

```yaml
nodeSelector:
  dockyard.pool: apps
```

**Node affinity** does the same with more options:

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: dockyard.pool
          operator: In
          values: [apps]
```

`required...` is a hard rule.
`preferredDuringScheduling...` is a preference the scheduler tries to honour.
"IgnoredDuringExecution" means changing a node’s labels later does not evict Pods already running there.

You add labels to nodes yourself with `kubectl label node NODE_NAME key=value`.

## Taints and tolerations: which Pods a node will accept

A **taint** on a node repels Pods:

```sh
kubectl taint nodes NODE_NAME dockyard.pool=apps:NoSchedule
kubectl taint nodes NODE_NAME dockyard.pool=apps:NoSchedule-
```

The first command adds the taint; the trailing `-` in the second removes it.
`NoSchedule` stops new Pods landing there; `NoExecute` also evicts Pods already running; `PreferNoSchedule` is a soft version.

A Pod can ignore a matching taint if it has a **toleration**:

```yaml
tolerations:
- key: dockyard.pool
  operator: Equal
  value: apps
  effect: NoSchedule
```

Here is the part people get wrong: a toleration only *allows* a Pod onto a tainted node.
It does not *send* it there.
To dedicate nodes to an application you need both: a taint to keep others off, and affinity (or a nodeSelector) to bring the application on.

```figure
taints-affinity
```

## Spreading copies across nodes

A **topology spread constraint** keeps copies from bunching up:

```yaml
topologySpreadConstraints:
- maxSkew: 1
  topologyKey: kubernetes.io/hostname
  whenUnsatisfiable: DoNotSchedule
  labelSelector:
    matchLabels: {app: dispatch, track: stable}
  matchLabelKeys: [pod-template-hash]
```

`topologyKey: kubernetes.io/hostname` treats each node as a separate group.
`maxSkew: 1` means no node may have more than one extra copy compared with another.
`DoNotSchedule` makes that a hard rule.
`matchLabelKeys: [pod-template-hash]` means each new rollout is spread on its own, ignoring old Pods on their way out.

Spread rules only act when a Pod is placed; Kubernetes does not move running Pods later to rebalance them.

```figure
topology-spread
```

## Priority: which Pods win when a cluster is full

A **PriorityClass** gives Pods a number: the higher it is, the more important they are.
When there is no room, the scheduler places higher-priority Pods first and may **preempt**, that is evict, lower-priority Pods to make space.

```sh
kubectl create priorityclass dispatch-critical --value=100000 --description="Core Dispatch services"
kubectl get priorityclass
```

A Pod opts in with `priorityClassName: dispatch-critical` in its spec; for a Deployment, that goes in the Pod template:

```sh
kubectl patch deployment dispatch -p '{"spec":{"template":{"spec":{"priorityClassName":"dispatch-critical"}}}}'
```

PriorityClasses belong to the whole cluster, not a namespace.
Kubernetes ships two for its own components, `system-cluster-critical` and `system-node-critical`; leave those to the system.
Use priority sparingly: if everything is high priority, nothing is.

## This lab

The cluster has a control-plane node and two worker nodes.
The workers carry the label `dockyard.pool=apps` and the taint `dockyard.pool=apps:NoSchedule`.
The database stays on the control-plane node here, so that draining a worker in a later lesson does not strand its storage.
That is a practice compromise, not a production recommendation.

```sh
kubectl get nodes --show-labels
kubectl describe node "$DOCKYARD_CLUSTER-worker" | grep -A3 Taints
kubectl describe pods -l app=dispatch,track=stable
kubectl get pods -l app=dispatch,track=stable -o wide
```

A Pending Pod’s `FailedScheduling` event says why each node was ruled out, for example “0/3 nodes are available: 3 node(s) had untolerated taint(s)”.
Each node is listed under the first rule it failed, so fixing one problem can reveal the next.
The control-plane node counts too: it carries its own `node-role.kubernetes.io/control-plane:NoSchedule` taint, which keeps ordinary workloads off it.
Read the event before changing anything.
All three nodes are containers on one computer, so spreading across them practises the scheduling rules without giving real protection against hardware failure.
