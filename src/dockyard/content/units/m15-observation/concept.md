## Three kinds of evidence

When something goes wrong in a cluster, there are three main places to look, and each answers a different question:

- **Events**: what did Kubernetes decide or notice? Scheduling failures, image pull errors, probe failures, restarts.
- **Logs**: what did the application say? Whatever the program writes to its output.
- **Metrics**: how is it behaving over time? Numbers such as request counts, error rates, and response times.

None of them replaces the others.
A Pod can be Running with healthy logs while serving every request slowly, and a broken metrics collector can make a healthy app look silent.

## Kubernetes’ own tools

These are what the CKA and CKAD exams expect you to use quickly:

```sh
kubectl get events --sort-by=.metadata.creationTimestamp
kubectl events --for deployment/dispatch
kubectl logs deployment/dispatch -c api --tail=30
kubectl logs -l app=dispatch --all-containers --prefix --since=10m
kubectl logs POD_NAME --previous
kubectl logs -f deployment/dispatch
kubectl top pods
kubectl top nodes
```

- `--sort-by` puts events in time order; `kubectl events --for` shows only one object’s events.
- `-c` picks a container, `--all-containers` shows them all, `--prefix` labels each line with its Pod and container, `-l` selects Pods by label, and `--since` limits how far back to look.
- `--previous` shows the logs from before the container last restarted, which is often where the crash message is.
- `-f` keeps following new lines; Control-C stops following.
- `kubectl top` needs the Metrics Server. The capacity module’s labs install it; this lab does not, so here it reports that the metrics API is not available.

When an image has no debugging tools, you can attach a temporary **ephemeral container** that shares the Pod’s processes and network:

```sh
kubectl debug -it POD_NAME --image=busybox --target=api --profile=general -- sh
```

Give it a Pod name, not a Deployment.
`--target=api` lets the debugging container see the `api` container’s processes, so `ps` inside it shows `python app.py`.
`--profile=general` picks a sensible set of permissions and avoids a warning about the old default.
The ephemeral container stays listed in the Pod’s spec afterwards; it disappears when the Pod is replaced.

## Dispatch’s own signals

Dispatch writes a structured `http_request` log line for each `GET /jobs`, with a request ID, the status, how long it took, and which Pod served it.
It also publishes numbers at `/metrics` in the format read by **Prometheus**, a widely used monitoring system that collects numbers from each target on a schedule, called **scraping**.

Three kinds of number are worth knowing:

- A **counter** only goes up, such as the total number of requests. It resets to zero when the process restarts.
- A **gauge** goes up and down, such as the number of jobs waiting.
- A **histogram** counts observations into buckets, such as “requests faster than 0.1 s, faster than 0.25 s, faster than 0.5 s…”.

Because counters reset, you look at how fast they grow rather than their raw value.
In Prometheus’s query language, `rate(dispatch_http_requests_total[2m])` is requests per second averaged over two minutes, and it copes with resets.
Dispatch’s latency histogram only counts real `/jobs` reads, not health checks.

## Finding every Pod to scrape

Prometheus asks the Kubernetes API for Pods and decides which to scrape with **relabel rules**:

```yaml
relabel_configs:
- source_labels: [__meta_kubernetes_pod_label_app]
  regex: dispatch
  action: keep
- source_labels: [__meta_kubernetes_pod_container_port_name]
  regex: http
  action: keep
- source_labels: [__meta_kubernetes_pod_name]
  target_label: pod
```

Each `keep` rule drops every candidate that does not match.
The second one keeps only the container port *named* `http`, so it must match the port name in the Deployment.
The last rule copies the Pod’s name into a `pod` label, so each Pod’s numbers stay separate.
Scraping through a Service instead would hit a different Pod each time and mix their counters together.

Prometheus runs with its own ServiceAccount, allowed only to read Pods in this namespace.

`up` is a special series Prometheus records for every target: 1 if the last scrape worked, 0 if it failed.
It tells you the target could be scraped, not that users are happy.

The supplied `monitoring.sh` loads your edited files into ConfigMaps and restarts Prometheus so it reads them.
This lab scrapes every five seconds so you see results quickly; real systems choose these settings much more carefully.
