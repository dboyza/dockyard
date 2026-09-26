# Names organize; selectors connect

A namespace scopes names for objects such as Pods, Services, and ConfigMaps.
Nodes and PersistentVolumes are cluster-scoped, so a namespace flag does not create a separate copy of those resources.
Namespaces are an organizational boundary; permissions and network policy provide the corresponding access controls.

Labels are arbitrary key-value metadata used to group objects.
A selector evaluates those labels, not the object's name.
A Service named `dispatch` can select Pods with any name, but it routes no requests if its selector matches no ready Pods.
Owner references are different again: they connect a dependent object to the controller responsible for its lifecycle.

## Worked example

```sh
kubectl get pods -n dispatch --show-labels
kubectl get pods -n dispatch -l app=dispatch
kubectl get service dispatch -o yaml
kubectl get endpointslices -l kubernetes.io/service-name=dispatch
kubectl get pods -A
```

Start with an all-namespace query when an object seems to be missing, then narrow the query explicitly.
EndpointSlices connect a Service to reachable Pod addresses and readiness conditions.
A correct-looking Service name is insufficient evidence of a working route.

The namespace called `default` is an ordinary default selection, not an administrator namespace.
`kube-system` hosts cluster components and should not be used for this application.
The lab's private kubeconfig selects `dispatch` so your normal application commands remain scoped.
