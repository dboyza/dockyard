# Exam technique for the CKA and CKAD

The CKA and CKAD are hands-on exams.
You get a real terminal, a set of clusters, and about two hours to complete a series of tasks.
Knowing Kubernetes is necessary but not enough: you also need to work quickly, carefully, and in the right place.
This guide collects the habits that make the difference.
Practise them in the lessons and the timed practice exams until they are automatic.

Exam rules and the exam environment change over time.
Before booking, read the current Linux Foundation candidate handbook and the CKA/CKAD instructions, including which documentation sites you may use.

## Before every task: context and namespace

Each task names a cluster context, and often a namespace.
Working in the wrong one is the easiest way to lose marks for work you did correctly.
Make the task’s context switch the first thing you do, every time:

```sh
kubectl config use-context CONTEXT_NAME
kubectl config set-context --current --namespace=NAMESPACE
kubectl config get-contexts
```

The last command marks the current context with `*` and shows its namespace.
If you prefer not to change the default namespace, add `-n NAMESPACE` to every command instead; just be consistent.

## Generate YAML instead of typing it

Never write a manifest from memory if kubectl can write it for you.
Generate a starting file, edit what you need, and apply it:

```sh
kubectl run web --image=nginx --labels=app=web --dry-run=client -o yaml > pod.yaml
kubectl create deployment web --image=nginx --replicas=3 --dry-run=client -o yaml > deploy.yaml
kubectl apply -f deploy.yaml
```

Many tasks can be finished entirely with imperative commands:

| Goal | Command |
| --- | --- |
| Pod | `kubectl run NAME --image=IMAGE` |
| Deployment | `kubectl create deployment NAME --image=IMAGE --replicas=N` |
| Service for a Deployment | `kubectl expose deployment NAME --port=P --target-port=T --type=TYPE` |
| ConfigMap | `kubectl create configmap NAME --from-literal=KEY=VALUE` |
| Secret | `kubectl create secret generic NAME --from-literal=KEY=VALUE` |
| Job | `kubectl create job NAME --image=IMAGE -- COMMAND` |
| CronJob | `kubectl create cronjob NAME --image=IMAGE --schedule="*/5 * * * *" -- COMMAND` |
| ServiceAccount | `kubectl create serviceaccount NAME` |
| Role | `kubectl create role NAME --verb=get,list --resource=pods` |
| RoleBinding | `kubectl create rolebinding NAME --role=ROLE --serviceaccount=NS:NAME` |
| Ingress | `kubectl create ingress NAME --rule="HOST/PATH=SERVICE:PORT"` |
| Change image | `kubectl set image deployment/NAME CONTAINER=IMAGE` |
| Scale | `kubectl scale deployment/NAME --replicas=N` |
| Add a label | `kubectl label pod NAME KEY=VALUE` |
| One-off test Pod | `kubectl run tmp --rm -it --image=busybox --restart=Never -- sh` |
| Debug a running Pod | `kubectl debug -it POD --image=busybox --target=CONTAINER -- sh` |
| Logs from before a restart | `kubectl logs POD --previous` |

`kubectl create --help` lists every type that `create` can make; `kubectl create deployment --help` shows its examples.

## Look things up without leaving the terminal

```sh
kubectl explain pod.spec.containers.readinessProbe
kubectl explain deployment.spec.strategy --recursive
kubectl api-resources
```

`explain` describes any field and what goes under it.
`--recursive` prints the whole tree of fields below one point, which is handy when you cannot remember a name.
`api-resources` lists every object type, its short name, and whether it lives in a namespace.

Short names save typing: `po` for pods, `deploy`, `svc`, `cm` for ConfigMaps, `sa` for ServiceAccounts, `pvc`, `pv`, `ns`, `ing` for Ingresses, and `netpol` for NetworkPolicies.

## Edit files quickly in vim

The exam terminal has `vim` and usually `nano`; practise in whichever you will use.
If you use vim, these commands cover most needs:

| Keys | Effect |
| --- | --- |
| `i` | start typing (insert mode) |
| `Esc` | stop typing (normal mode) |
| `:wq` | save and quit |
| `:q!` | quit without saving |
| `dd` | delete the current line |
| `yy` then `p` | copy the current line, then paste it below |
| `u` | undo |
| `/text` | search for text |
| `:set paste` | paste YAML without vim re-indenting it |

A small `~/.vimrc` helps with YAML:

```text
set expandtab tabstop=2 shiftwidth=2
```

When an object has no file, `kubectl edit deployment NAME` opens the live object in your editor.
Some fields cannot be changed on a running Pod; kubectl then saves your edited copy to a temporary file, and `kubectl replace --force -f THAT_FILE` deletes and recreates the Pod with your changes.

## Check every task before moving on

A task is only done when the result works, not when a command succeeded.

- For a workload: `kubectl get pods` shows it Running and Ready, and `kubectl describe` shows no warning events.
- For a Service: `kubectl get endpointslices -l kubernetes.io/service-name=NAME` lists the Pods, and a request from a test Pod reaches them.
- For permissions: `kubectl auth can-i VERB RESOURCE --as=system:serviceaccount:NS:NAME`.
- For a file the task asked you to write: `cat` it.

Output formats help you check exactly what was asked:

```sh
kubectl get pods -o wide
kubectl get pods --show-labels
kubectl get pod NAME -o jsonpath='{.spec.containers[*].image}'
kubectl get pods -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeName
kubectl get pods --sort-by=.metadata.creationTimestamp
```

## Managing the clock

- Read each task fully before starting; note its context, namespace, names, and any file you must write.
- Do quick tasks first. If one is taking much longer than its share of the time, flag it and move on.
- Tasks carry different weights; a partly finished heavy task can be worth less than two finished light ones.
- Leave a few minutes at the end to revisit flagged tasks.
- Delete a stuck Pod with `kubectl delete pod NAME --grace-period=0 --force` only when you are sure it is yours and safe to remove; waiting for graceful shutdown can cost time.

## Practising in Dockyard

Every lesson in this course practises these commands on a real cluster.
The four timed practice exams give you the same pressure: two hours, many tasks, and a score at the end.
They are original practice, not copies of the real exams, and a score here is not a prediction of your result.
When a practice exam shows a weak area, the results link back to the lessons that teach it.
