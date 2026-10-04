## When the node is full

Requests reserve room on a node, as you saw earlier in this module.
Once every bit of a node's room is reserved, a new Pod has nowhere to go.
It stays **Pending**, and its Events say why, for example `Insufficient cpu`.

Sometimes that is the right outcome: the Pod waits until something finishes.
But not all work is equally urgent.
If an overnight report has filled the node, the Dispatch API, which users are waiting on, should not be the one left waiting.

## Priority and preemption

A **PriorityClass** is a named number.
Pods choose one with `priorityClassName`, and Kubernetes copies its value into the Pod's `spec.priority` when the Pod is created.
Higher numbers mean more important.

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: batch-low
value: 1000
globalDefault: false
description: Work that can be displaced when something more important needs room.
```

Priority affects scheduling in two ways.
Pending Pods are considered in priority order, so important Pods are placed first.
And if a high-priority Pod still cannot fit anywhere, the scheduler can **preempt**: it removes enough lower-priority Pods from one node to make room, then places the important Pod there.

Step through the figure to follow one preemption.

```figure
priority-preemption
```

The preempted Pods are not lost.
Their Deployment still wants them, so it creates replacements, which wait as Pending until room returns.
Nothing was scaled down; the cluster simply decided which work waits.

Two settings deserve care:

- `globalDefault: true` gives the class to every new Pod that does not name one, which quietly raises the priority of everything.
- `preemptionPolicy: Never` lets a class jump the queue without ever displacing running Pods.

## This lab's node

So the lab behaves identically on every computer, the node advertises exactly four **slots**, an extended resource called `dockyard.io/slots`.
Extended resources are a real Kubernetes feature for counting things the node has, such as attached devices.
Each batch Pod and each API Pod requests one slot.
Real clusters run out of CPU or memory, and priority works the same way there.

## See the shortage

Prepare the lab, then look at what is running and what is waiting:

```sh
kubectl get pods -o custom-columns=NAME:.metadata.name,PRIORITY:.spec.priority,STATUS:.status.phase
kubectl describe node | grep -A2 dockyard.io/slots
```

Three `report-batch` Pods hold three slots with priority 1000, one API Pod holds the fourth, and the second API Pod is Pending.
Run `kubectl describe pod` on the Pending API Pod and read the last Events line, which reports `Insufficient dockyard.io/slots`.
The API Pods show no priority value, so they cannot preempt anything.

## Fix it

1. Create `priority.yaml` with a PriorityClass for the API: a value higher than 1000 and `globalDefault: false`.
2. In `platform.yaml`, add `priorityClassName` with that class's name under the `dispatch` Deployment's Pod template `spec`.
3. Run `sh run.sh`; it applies `priority.yaml` when the file exists.

Watch it happen with `kubectl get pods -w`, then press Control-C.
You should see one `report-batch` Pod terminate, a new API Pod start in its place, and a replacement batch Pod appear as Pending.
`kubectl get events --field-selector reason=Preempted` lists the displaced Pod.

Do not scale or delete `report-batch`, and do not lower the API's slot request.
Those would free room, but they would not show priority doing its job.

## If something goes wrong

- **The API Pod is still Pending**: check its `spec.priority` with the custom columns above. No value means `priorityClassName` is not under the Pod template's `spec`, or the class name is misspelled.
- **`priorityClassName` is rejected**: the PriorityClass must exist before the Deployment refers to it; `run.sh` applies `priority.yaml` first.
- **Batch Pods keep getting displaced**: a class with `globalDefault: true` raised their replacements too. Set it to `false`.
