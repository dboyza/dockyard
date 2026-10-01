## Tell Kubernetes what should keep running

With Docker, you started a container yourself.
If you removed it, you had to create another one.
Kubernetes can keep the application running for you: you tell it how many copies you want, and it works to maintain that number.
This is called **reconciliation**: comparing what you asked for with what exists, then correcting the difference.

In this lesson, you’ll ask for two copies of Dispatch, remove one, and watch Kubernetes replace it.
You’ll use a small private **cluster**, a group of machines that Kubernetes manages.
Dockyard prepares it for you using one local machine called a **node**.

## Meet the three objects you’ll inspect

A **Pod** holds one or more containers that run together and share networking.
Here, each Pod holds one Dispatch container.
A **ReplicaSet** keeps a specified number of matching Pods running.
A **Deployment** manages the ReplicaSet and controls updates to the application.
You edit the Deployment rather than creating each Pod by hand.

A **Service** gives requests a stable destination even when the Pods change.
Later lessons explain how it finds the right Pods.
For now, keep the supplied Service settings unchanged.

## Read the starting state

Prepare the lab, then open its lab terminal.
The command-line tool **kubectl** sends your requests to the Kubernetes API.
Dockyard has already selected this lab’s cluster and its `dispatch` **namespace**, a named group of resources within the cluster.
The `-n dispatch` option makes that namespace explicit.

```sh
kubectl get deployments,replicasets,pods -n dispatch
kubectl describe deployment dispatch -n dispatch
```

The starter Deployment asks for zero copies, so you should see `0/0` ready and no Dispatch Pods.
That is not a crash: Kubernetes is doing exactly what the file asked it to do.
`get` gives you a short table; `describe` gives you more detail, including recent events.

## Change the requested number of copies

Open `deployment.yaml` in your editor.
This is a **manifest**, a text file describing a Kubernetes object in YAML.
Find `replicas: 0` under `spec` and change the number to `2`.
Keep the indentation and the other settings unchanged.
Use the YAML guide above if this file format is unfamiliar.

Run the supplied script, then wait for the Deployment:

```sh
sh run.sh
kubectl rollout status deployment/dispatch -n dispatch --timeout=90s
kubectl get pods -n dispatch -l app=dispatch -o wide
```

`sh run.sh` runs the script in your workspace.
It replaces the image placeholder with this lab’s image and sends your files to Kubernetes using `kubectl apply`.
An `apply` success means the API accepted your request, not that the containers have finished starting.
`rollout status` waits for the Deployment to become available.
The final command lists Pods with the label `app=dispatch`; `-o wide` includes their IP addresses and node names.
Look for two Pods with `1/1` in the READY column.

Before deleting a real Pod, rehearse the idea in this simplified model.
Delete a Pod, then advance the controller one step at a time and watch the observed count return to the desired count.

```figure
reconciliation-model
```

## Predict what happens when a Pod disappears

Choose one Pod name from that table.
In the commands below, replace `POD_NAME` with that actual name.
Write down its UID, the unique identifier for that particular Pod:

```sh
kubectl get pod POD_NAME -n dispatch -o jsonpath='{.metadata.uid}'
kubectl delete pod POD_NAME -n dispatch
kubectl get pods -n dispatch -w
```

The last command keeps watching for changes.
Press Control-C once the replacement is ready; that stops the watch, not the Pods.
The old Pod may disappear before you see it in the list, but the replacement has a new name and UID.
The Deployment still asks for two copies, so Kubernetes creates another Pod to make up the difference.

Deleting the Deployment would be different: it removes the instruction to keep those copies running, along with its dependent ReplicaSet and Pods.
Do not delete it for this task.
Two Pods on this single node also do not protect against losing the node itself; we’ll explore that distinction later.
