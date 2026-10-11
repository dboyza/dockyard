## Requests without credentials

Every request to the API server passes **authentication**, which decides who is asking, before **authorization**, which decides whether they may do it.
You have worked with authorization through RBAC; this lesson is about the step before it.

A request may carry no credentials at all: no client certificate and no token.
By default, the API server does not reject it.
It treats the caller as the user `system:anonymous` in the group `system:unauthenticated`, and passes the request on to RBAC.
This exists so that health checks and a little discovery information work without credentials.
Kubernetes grants anonymous callers very little by default, but any RoleBinding or ClusterRoleBinding that names that user or group hands its permissions to everyone who can reach the API server.

```figure
anonymous-requests
```

Try it from your terminal, where `$DOCKYARD_API_PORT` is this lab's API server port.
`-k` skips certificate checking because no credentials or CA are given:

```sh
curl -sk "https://127.0.0.1:$DOCKYARD_API_PORT/api/v1/namespaces/dispatch/configmaps" | head -20
```

The ConfigMaps list comes back, with no credentials at all.
To find out why, list the bindings and look for anonymous subjects:

```sh
kubectl get clusterrolebindings -o wide | grep -E 'system:(anonymous|unauthenticated)'
```

Bindings named `system:...` or `kubeadm:...` are defaults that Kubernetes and kubeadm create.
Anything else deserves a question.

## Two layers of defense

Removing the bad binding fixes today's problem.
But anonymous requests still reach RBAC, so the next careless binding would reopen it.
The stronger fix also limits which requests may be anonymous in the first place.

The API server reads an **authentication configuration** file, passed with `--authentication-config`.
Its `anonymous` section can keep anonymous access only for the health endpoints that load balancers and monitoring call without credentials:

```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: AuthenticationConfiguration
anonymous:
  enabled: true
  conditions:
  - path: /livez
  - path: /readyz
  - path: /healthz
```

Any other request without credentials is now rejected during authentication with **401 Unauthorized**, before RBAC is even consulted.
A **403 Forbidden** would mean the opposite: the caller was identified, as anonymous or otherwise, and RBAC said no.

The older `--anonymous-auth=false` flag turns anonymous access off completely, which also breaks health checks that run without credentials.
You cannot use both the flag and the `anonymous` section at once.

## Giving a static Pod a new file

The API server runs as a static Pod from `/etc/kubernetes/manifests/kube-apiserver.yaml`, inside its own container.
A file you create on the node is not visible inside that container until the manifest mounts it.
That takes three edits:

```figure
static-pod-mounts
```

```yaml
spec:
  containers:
  - command:
    - kube-apiserver
    - --authentication-config=/etc/kubernetes/auth-config.yaml
    # ...the existing flags...
    volumeMounts:
    - name: auth-config
      mountPath: /etc/kubernetes/auth-config.yaml
      readOnly: true
  volumes:
  - name: auth-config
    hostPath:
      path: /etc/kubernetes/auth-config.yaml
      type: File
```

Keep every existing flag, mount, and volume, and add these alongside them.
`type: File` makes the kubelet refuse to start the Pod if the file is missing, which is a clearer failure than an empty directory appearing in its place.

## Fix it

1. Use `curl` and `kubectl get clusterrolebindings -o wide` to find the binding that exposes data, and delete it and its ClusterRole.
2. On the control-plane node, create `/etc/kubernetes/auth-config.yaml` with the configuration above, using `sudo`.
3. Add the flag, the volume mount, and the volume to the API server's manifest.
4. Wait for `kubectl get --raw=/readyz` to print `ok`, then repeat the `curl` request: it should return a 401 status.
5. Confirm `curl -sk "https://127.0.0.1:$DOCKYARD_API_PORT/readyz"` still prints `ok`.

## If something goes wrong

- **kubectl stops answering for more than a couple of minutes**: the API server is not starting. On the control plane, `sudo crictl ps -a --name kube-apiserver` and `sudo crictl logs` on the newest container show why; a YAML mistake or a file path that does not match the mount is the usual cause.
- **The ConfigMaps request returns 403 instead of 401**: the binding is gone, but anonymous requests are still accepted. The authentication configuration is not in effect yet.
- **`/readyz` returns 401 too**: the `conditions` list is missing the health paths, or the old `--anonymous-auth=false` flag is set.
