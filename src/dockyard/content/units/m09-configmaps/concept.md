## Change settings without rebuilding the image

The same Dispatch image should run in development, testing, and production.
What differs between them, such as which environment name to show or which features to switch on, is **configuration**.
Kubernetes stores ordinary configuration in a **ConfigMap**: a named set of keys and values in one namespace.

## Creating a ConfigMap

You can write one in YAML:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: dispatch-settings
data:
  environment: learning
  banner.txt: |
    Configured through the Kubernetes API.
```

Or create one directly, which is faster in exams:

```sh
kubectl create configmap demo --from-literal=environment=learning --from-file=banner.txt
```

`--from-literal` adds a key with the value you type; `--from-file` adds a key named after the file, holding its contents.
Add `--dry-run=client -o yaml` to see the YAML instead of creating it.

## Two ways a container can use it

**As environment variables.**
Pick one key with `configMapKeyRef`:

```yaml
env:
- name: DISPATCH_ENV
  valueFrom:
    configMapKeyRef:
      name: dispatch-settings
      key: environment
```

Or load every key at once with `envFrom: [{configMapRef: {name: dispatch-settings}}]`.

**As files.**
Mount the ConfigMap as a volume, and each key becomes a file:

```yaml
volumes:
- name: settings
  configMap:
    name: dispatch-settings
    items:
    - key: banner.txt
      path: banner.txt
```

`items` is optional; it chooses which keys to include and what file name each gets.
Mount the volume in the container with `volumeMounts` as usual, for example at `/config`.

## When do changes reach the application?

This is the part people get wrong.

- **Environment variables are read once**, when the container starts. Editing the ConfigMap changes nothing in running containers. You must replace the Pods, for example with `kubectl rollout restart deployment/dispatch`.
- **Mounted files are updated** by Kubernetes, usually within a minute or two, but only if the application reads the file again. A mount that uses `subPath` never receives updates.

Dispatch’s `/config` address shows both: the environment name it read at startup, and the banner file, which it reads fresh on every request.

## This lab

The API’s Deployment sets `DISPATCH_ENV` to the literal value `stale` instead of reading the ConfigMap, and it mounts the `environment` key as `banner.txt` instead of the real banner.
Compare what the ConfigMap holds with what the Deployment actually uses:

```sh
kubectl get configmap dispatch-settings -o yaml
kubectl get deployment dispatch -o yaml | grep -A20 'env:'
kubectl exec deployment/dispatch -c api -- cat /config/banner.txt
```

After fixing `platform.yaml` and running `sh run.sh`, check the result through the Service with a port-forward:

```sh
kubectl rollout status deployment/dispatch --timeout=90s
kubectl port-forward service/dispatch 18080:8080 &
curl http://127.0.0.1:18080/config
kill %1
```

## Note on Service variables

Kubernetes normally injects extra environment variables describing every Service, such as `DB_PORT`.
Those can clash with an application’s own settings, so this lab turns them off with `enableServiceLinks: false`.
Services are still reachable by name through DNS.
