## Pick the right kind of controller

A Deployment is not the only way to run Pods.
Kubernetes has several **workload controllers**, each built for a different kind of work.
Choosing the right one is a core exam skill, and it saves you from fighting the tool.

| Controller | Use it for | How many Pods |
| --- | --- | --- |
| **Deployment** | long-running, interchangeable copies, such as Dispatch’s API and workers | the number you ask for |
| **DaemonSet** | one helper on every suitable node, such as a log collector | one per matching node |
| **Job** | a task that runs until it finishes, such as a data import | until it succeeds |
| **CronJob** | a Job that runs on a schedule, such as a nightly cleanup | one Job per scheduled time |
| **StatefulSet** | copies that each need a stable name and their own storage, such as databases | the number you ask for |

A Pod created on its own, with no controller, is called a **bare Pod**.
Nothing replaces it if it is deleted or its node fails, so avoid them for real work.

```figure
workload-controllers
```

Dispatch’s workers are a good fit for a Deployment: any worker can take any job, and they coordinate through the database, not through memory.

## This lab

Dispatch’s API, database, and Redis queue are already running.
Two things are wrong:

- The `worker` Deployment asks for zero copies, so nobody processes jobs.
- The `dispatch-node-agent` DaemonSet has a **node selector**, a rule saying which nodes it may run on, that matches no node at all.

Look before you change anything:

```sh
kubectl get deployments,daemonsets
kubectl describe daemonset dispatch-node-agent
kubectl get nodes --show-labels
```

For a DaemonSet, `DESIRED` is the number of nodes it is allowed to run on.
Here it is 0, because no node has the label `dockyard.invalid/node=missing`.
A DaemonSet has no replicas setting to increase; you fix it by changing where it is allowed to run.

```figure
daemonset-selector
```

## Two ways to change the worker count

You can edit `replicas:` in `worker.yaml` and apply it, which keeps your file up to date.
Or you can change the live object directly:

```sh
kubectl scale deployment worker --replicas=2
```

`kubectl scale` is quick, and handy in exams, but it leaves your file saying something different from the cluster.
In this lab, change the file so the two stay in step.

## Watch a job get done

After applying your changes and waiting for the rollouts, submit a job through the API and read a worker’s logs:

```sh
kubectl rollout status deployment/worker --timeout=90s
kubectl rollout status daemonset/dispatch-node-agent --timeout=90s
```

The API runs inside the cluster, so your terminal cannot reach it directly.
`kubectl port-forward` opens a temporary tunnel from a port on your computer to a Service or Pod:

```sh
kubectl port-forward service/dispatch 18080:8080 &
curl -H 'Content-Type: application/json' -d '{"title":"hello workers"}' http://127.0.0.1:18080/jobs
kubectl logs deployment/worker --tail=20
kill %1
```

`18080:8080` means “port 18080 on my computer goes to port 8080 of the Service”.
kubectl uses the Service only to pick one of its Pods, then connects straight to that Pod, so the tunnel does not spread requests across Pods.
Any free port on your computer will do; if 18080 is already in use, the command says so, and you can pick another.
The `&` runs the tunnel in the background so you can keep typing; `kill %1` closes it when you are done.
The worker’s log should show your job being completed.
Port-forwarding is for testing and debugging; real users reach applications through Services and Ingress, which later lessons cover.

```figure
port-forward
```

## Generate these objects quickly

kubectl can write starting YAML for most controllers:

```sh
kubectl create deployment web --image=nginx --replicas=3 --dry-run=client -o yaml
kubectl create job import --image=busybox --dry-run=client -o yaml -- echo done
kubectl create cronjob cleanup --image=busybox --schedule="0 2 * * *" --dry-run=client -o yaml -- echo tidy
```

There is no `kubectl create daemonset`; the usual trick is to generate a Deployment, change `kind` to `DaemonSet`, and delete `replicas` and `strategy`.

## A note on the database

The database in this lab keeps its data in an `emptyDir` volume, which is deleted along with its Pod.
That keeps this lesson focused on controllers; the storage module replaces it with real persistent storage.
