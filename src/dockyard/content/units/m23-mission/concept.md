## A bad day for the control plane

Several things have gone wrong on the control-plane node at once:

- kubectl cannot reach the API server;
- even once it can, the cluster will not be able to place new Pods;
- an original ConfigMap, `maintenance-sentinel` in the `default` namespace, has been deleted.

Luckily, a snapshot was taken before the deletion.
It is on the control-plane node at `/var/lib/etcd/dockyard-recovery.db`.
Dispatch's database is still safe on its volume on the worker.

Your job is to recover this cluster, not to build a new one.
Everything you need was taught in the three lessons of this module.

## Plan before you act

Think about the order.
Which tools still work while the API is down?
Which fixes depend on others?
Restoring etcd rolls the whole API back to the moment of the snapshot, so decide whether you would do it before or after your other fixes, and why.

Look before you change anything, and write down what you find at each layer: the kubelet service, the static Pod files, the running containers, and the API.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.

## Your handoff

In `handoff.md`, write for the next person on call:

- what was wrong at each layer, and the evidence that showed it;
- the order you fixed things in, and why;
- how you showed the sentinel is the original object, that new Pods get scheduled, and that a new job completes;
- what the etcd snapshot covers and what it does not, compared with the database on the worker;
- what a production recovery plan would add, for example more than one control-plane node and backups stored off the node.

Keep credentials, certificates, and the snapshot itself out of the handoff.
Check work tests the cluster; the handoff is for you to compare with the debrief.
