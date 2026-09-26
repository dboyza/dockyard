# The API is a declaration of intent

A Docker command asks one daemon to start one container.
A Kubernetes Deployment records the number of application replicas you want the cluster to maintain.
The API server stores that declaration; controllers repeatedly compare it with observed state and act to reduce the difference.
This reconciliation is asynchronous, so a successful `kubectl apply` does not mean the application is ready.

A Deployment owns ReplicaSets, and each ReplicaSet owns Pods.
A Pod groups containers that share networking and can share volumes; it is the scheduling unit.
The scheduler selects a node for an unscheduled Pod, and that node's kubelet asks its container runtime to run the containers.
Replacing a Pod gives it a new identity and usually a new IP.
A Service supplies a stable destination for a changing set of Pods.

## Worked example

```sh
kubectl get deployments,replicasets,pods -n dispatch
kubectl describe deployment dispatch
kubectl get pods -l app=dispatch -o wide
kubectl get events --sort-by=.metadata.creationTimestamp
```

The first command shows related objects, not a single flat process list.
Compare a Deployment's desired replicas with ready and available replicas before claiming that a rollout succeeded.
`kubectl describe` includes conditions and events that explain why progress stopped.

## Observe replacement

After repairing the exercise, record one Pod's UID with `kubectl get pod NAME -o jsonpath='{.metadata.uid}'`.
Delete that single practice Pod and watch `kubectl get pods -w` until a replacement is ready.
Deleting the Pod leaves the Deployment's desired replica count intact, so its controller creates another Pod.
Deleting the Deployment would remove that desired state and its dependent ReplicaSets and Pods.
