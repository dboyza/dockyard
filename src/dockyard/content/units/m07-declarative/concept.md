## Make changes on purpose, in the right place

So far you have applied files that were mostly written for you.
This lesson covers three habits that keep you safe, and fast, when you change a cluster yourself:
knowing which cluster you are talking to, checking a change before applying it, and generating YAML instead of typing it from memory.

## Which cluster am I talking to?

kubectl reads a **kubeconfig** file to know which clusters exist, how to log in to each, and which one to use.
A **context** is a saved combination of a cluster, a login, and a default namespace.
Whichever context is **current** receives every command you type.

```figure
kubeconfig-contexts
```

```sh
kubectl config current-context
kubectl config get-contexts
kubectl config view --minify
```

The first prints the current context’s name.
The second lists all contexts, marking the current one with `*`.
The third shows only the current context’s settings; look for its `namespace`.

Dockyard gives each lab its own kubeconfig through the `KUBECONFIG` variable, so your personal kubeconfig is never touched.

In the certification exams, each question tells you which context to use, and forgetting to switch is one of the most common ways to lose marks.
The two commands to remember are:

```sh
kubectl config use-context CONTEXT_NAME
kubectl config set-context --current --namespace=NAMESPACE
```

The first switches to a different context; the second changes the default namespace of the current one.
This lab has only one context, so there is nothing to switch to, but get into the habit of checking before every change.

## Check a change before you apply it

```sh
python render.py deployment.yaml | kubectl diff -f -
python render.py deployment.yaml | kubectl apply --dry-run=server -f -
```

`render.py` fills in this lab’s image name, and the `|` passes the result to kubectl, where `-f -` means “read the file from the pipe”.
`kubectl diff` shows what would change in the live object.
It exits with status 1 when there are differences, which is normal.
`--dry-run=server` sends the object to the cluster for full checking without saving it, so you find mistakes before anything changes.

```figure
change-workflow
```

After a real `apply`, remember that acceptance is not the same as success: `kubectl rollout status` tells you when the new Pods are actually running.

## Editing a live object

Sometimes an object was created by hand and has no file, or you just need a quick change.
`kubectl edit` opens the live object in a text editor and applies your change when you save and close:

```sh
KUBE_EDITOR=nano kubectl edit service dispatch
```

`KUBE_EDITOR=nano` picks the editor for this one command; without it, kubectl uses your `EDITOR` setting, or `vi` if none is set.
If your edit is invalid, kubectl reopens the file with an error message at the top.
Remember that a live edit leaves your workspace files out of date, so prefer editing the file and applying it when one exists.

## API versions change over time

Every manifest starts with `apiVersion` and `kind`.
Together they tell Kubernetes which version of which object type the file describes.
Kubernetes retires old versions: Deployments were once `extensions/v1beta1`, but modern clusters only accept `apps/v1`.
A file written for a retired version is rejected, whatever namespace or context you use.

To see which versions your cluster serves:

```sh
kubectl api-resources | grep -i deployment
kubectl explain deployment
```

`api-resources` lists every object type with its API group; `explain` shows the version it describes at the top.
When you migrate a file, change `apiVersion`, and check with `kubectl explain` that the fields you use still exist.
For Deployments, `apps/v1` requires a `spec.selector` that matches the Pod template’s labels.

## Generate YAML instead of writing it

Typing a Deployment from memory is slow and error-prone.
kubectl can write a correct starting file for you:

```sh
kubectl create deployment demo --image=nginx --replicas=2 --dry-run=client -o yaml
```

`--dry-run=client` means “don’t send anything to the cluster”, and `-o yaml` prints the object instead.
Add `> demo.yaml` to save it, edit what you need, then apply it.
The same trick works for many types, such as `kubectl run`, `kubectl create service`, and `kubectl create configmap`.
You will use it constantly in the exams.
