## Trying a new release on a little traffic first

A rolling update replaces every Pod with the new version.
Sometimes you want to be more careful: run the new version alongside the old one, send it a small share of real traffic, and watch before going further.
Two common patterns do this with plain Kubernetes objects.

## Canary releases

A **canary** runs a few Pods of the new version next to the stable Pods.
You use two Deployments, told apart by a label such as `track`:

- `dispatch` runs the stable release with labels `app=dispatch, track=stable`.
- `dispatch-canary` runs the candidate with labels `app=dispatch, track=canary`.

Each Deployment’s selector includes its `track`, so each only manages its own Pods.
The main `dispatch` Service selects only `app=dispatch`, so it sends traffic to *both* tracks.
With two stable Pods and one canary Pod, roughly a third of connections reach the canary.

It is only roughly.
Services balance connections, not individual requests, and clients that reuse a connection keep hitting the same Pod.
For exact percentages you need a routing layer with traffic weights, such as Gateway API’s `backendRefs` weights.

A second Service, `dispatch-preview`, selects `track=canary` only, so you can test the candidate directly before it gets any real traffic.

## Blue-green releases

**Blue-green** keeps two complete copies, blue (current) and green (new).
The Service points at one of them through its selector.
After testing green, you switch the selector, and all traffic moves at once.
Switching back is just as quick, but you need capacity for two full copies.

## Deciding whether to promote

Before you start, decide what would make you stop: error rates, slow responses, wrong data, or alerts.
Promote by moving the stable Deployment to the new image and removing the canary; abort by scaling the canary to zero.

## This lab

Prepare has already built the candidate image, whose release is `dispatch-release-2`.
But `dispatch-canary` asks for zero replicas, and `dispatch-preview` selects the stable track instead of the canary.
After editing, `sh run.sh` applies everything again.

```sh
kubectl get deployments,pods -l app=dispatch -L track
kubectl get endpointslices -l kubernetes.io/service-name=dispatch
kubectl get endpointslices -l kubernetes.io/service-name=dispatch-preview
kubectl exec deployment/dispatch -c api -- python -c 'import urllib.request; print(urllib.request.urlopen("http://dispatch-preview:8080/healthz").read().decode())'
```

`-L track` adds a column showing each Pod’s `track` label.
The preview request should report `dispatch-release-2`; requests to `dispatch` can report either release.
