## How does a Service find its Pods?

In the last lesson, a Service called `dispatch` sent requests to Dispatch’s Pods, and you left it alone.
Now you’ll see how it chooses those Pods, and what happens when it chooses wrongly.
Along the way you’ll learn the inspection commands you will use in every Kubernetes lesson from here on, and in the exams.

## Namespaces

A **namespace** is a named area inside a cluster.
Two objects can share a name if they are in different namespaces.
Most everyday objects, such as Pods, Deployments, and Services, belong to a namespace.
A few, such as nodes, belong to the whole cluster.

This lab’s terminal already uses the `dispatch` namespace, so plain `kubectl get pods` looks there.
Add `-n NAME` to look in another namespace, or `-A` to look in all of them:

```sh
kubectl get pods -A
```

You will see Kubernetes’ own components in `kube-system`.
Leave that namespace alone; it is not a place for applications.
`default` is simply the namespace used when none is chosen; it is not special.

When something seems to be missing, try `-A` first: it may just be in a different namespace.

## Labels and selectors

A **label** is a short `key=value` tag attached to an object, such as `app=dispatch`.
Labels mean nothing to Kubernetes on their own; they are for finding and grouping things.

A **selector** is a rule that picks objects by their labels.
A Service’s selector decides which Pods receive its traffic.
It looks only at labels, never at names: a Service called `dispatch` has no idea that a Deployment is also called `dispatch`.

```sh
kubectl get pods --show-labels
kubectl get pods -l app=dispatch
kubectl get service dispatch -o yaml
```

`--show-labels` adds a column listing each Pod’s labels.
`-l app=dispatch` shows only Pods with that label; it is the same kind of selection a Service makes.
`-o yaml` prints the whole object as YAML. Find `spec.selector` in the Service’s output.

## Endpoints: the Service’s current list of Pods

Kubernetes keeps a list of the ready Pod addresses each Service is sending traffic to, stored in objects called **EndpointSlices**:

```sh
kubectl get endpointslices -l kubernetes.io/service-name=dispatch
```

If the ENDPOINTS column is empty, the Service has nowhere to send requests, however correct its name looks.
That is the first thing to check when a Service “doesn’t work”.

## Who owns a Pod?

Labels group things, but **owner references** record which object created which.
A Pod made by a Deployment is owned by a ReplicaSet, which is owned by the Deployment:

```sh
kubectl get pods -o custom-columns=NAME:.metadata.name,OWNER:.metadata.ownerReferences[0].name
```

`custom-columns` lets you print exactly the fields you want, which is handy in exams.
Ownership tells you where to make a lasting change: edit the Deployment, not its Pods.

## Look up any field

Forgotten where a setting lives?
`kubectl explain` describes the fields of any object, without leaving the terminal:

```sh
kubectl explain service.spec.selector
kubectl explain deployment.spec.template.metadata.labels
```

In the certification exams, `kubectl explain` is one of your fastest references.

## Test from inside the cluster

A Service name only works from inside the cluster.
To test it, run a command inside one of Dispatch’s containers with `kubectl exec`:

```sh
kubectl exec deployment/dispatch -- python -c 'import urllib.request; print(urllib.request.urlopen("http://dispatch:8080/healthz").read().decode())'
```

`deployment/dispatch` tells kubectl to pick one of that Deployment’s Pods.
Everything after `--` runs inside the container.
Python is used here because the Dispatch image does not include curl.
