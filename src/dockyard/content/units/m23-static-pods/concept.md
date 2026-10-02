## Static Pods and the kubelet

Most Pods are created through the API: a controller asks for them, the scheduler picks a node, and that node's kubelet starts them.
The control plane cannot work that way, because the API server, scheduler, and etcd must run before the API exists.

So they run as **static Pods**.
The kubelet watches a directory on the node, usually `/etc/kubernetes/manifests`, and runs every Pod manifest it finds there, with no API involved.
The directory is set by `staticPodPath` in the kubelet's configuration file, `/var/lib/kubelet/config.yaml`.
Adding a file starts a Pod; removing it stops the Pod; editing it restarts the Pod with the new settings.

For each static Pod, the kubelet also creates a **mirror Pod** in the API so that `kubectl get pods -n kube-system` can show it.
The mirror is only a read-only reflection.
Deleting it with kubectl does not stop the real Pod, and the kubelet soon recreates the mirror.
To change a static Pod, you change its file on the node.

Creating your own static Pod is a common exam task:
generate a manifest with `kubectl run NAME --image=IMAGE --dry-run=client -o yaml`, then save it into the node's static Pod directory.

## This lab: two things broke

Two separate things have happened on the control-plane node:

- the scheduler's manifest was moved out of `/etc/kubernetes/manifests` to `/var/lib/dockyard/recovery/kube-scheduler.yaml`, so the scheduler stopped;
- then the kubelet itself was stopped.

Each fix needs the other.
Starting the kubelet will not bring back a scheduler whose file is missing, and putting the file back does nothing while no kubelet is watching the directory.

```figure
static-pod-repair
```

Notice also what keeps working.
Containers that were already running carry on without the kubelet, and Pods that already have a node keep running without the scheduler.
So "my existing Pods are fine" says nothing about whether the cluster can start anything new.

## Worked example: check each piece

```sh
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" systemctl status kubelet
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo journalctl -u kubelet -n 40 --no-pager
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo ls /etc/kubernetes/manifests
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo crictl ps -a
```

- `systemctl status` shows whether the kubelet service is running.
- `journalctl` shows its recent log, including whether it was stopped on purpose or crashed.
- `ls` shows which static Pod files exist; a healthy kubeadm control plane has four: etcd, the API server, the controller manager, and the scheduler.
- `crictl ps -a` shows which containers are really running on the node.

Now compare with what the API says: `kubectl get pods -n kube-system` may still show the scheduler as `Running`.
That status is only as fresh as the kubelet's last report, and a stopped kubelet reports nothing.
When the API and the node disagree, trust the node.

## Repair

Move the scheduler's file back into `/etc/kubernetes/manifests/kube-scheduler.yaml`, then start the kubelet with `sudo systemctl start kubelet`.
Keep any backup copies outside the manifests directory.

## Ask the scheduler for something new

The real test is whether a brand-new Pod gets a node.
In the lab terminal, run `python wait-control-plane.py`.
It retries until the API answers a read and a write and a fresh test Pod is scheduled, then removes that Pod.
You can test it yourself too:

```sh
kubectl run sched-test -n default --image=busybox --restart=Never -- sleep 60
kubectl get pod sched-test -n default -o wide
kubectl delete pod sched-test -n default --now
```

The `NODE` column shows where the scheduler placed it; with the scheduler stopped it would stay empty and the Pod `Pending`.
Use `-n default` here: the lab's usual namespace, `dispatch`, only accepts Pods with strict security settings, so a quick test Pod would be refused there.

Check work looks at the real processes on the node, checks the API is ready, schedules its own new Pod, and sends a new Dispatch job.
