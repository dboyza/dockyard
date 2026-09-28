## Start the controller and watch it repair drift

The CRD and the `dispatch` WorkerPool exist, but the controller Deployment is scaled to zero, so nothing acts on the pool.

1. Look at the WorkerPool and the controller’s ServiceAccount and Role. Notice that `dispatch-workers` does not exist yet: nothing has acted on the pool.
2. Set the controller to one replica in `operator.yaml`, apply it with `python render.py operator.yaml | kubectl apply -f -`, and wait for the WorkerPool’s `Ready` condition.
3. Check who owns the new `dispatch-workers` Deployment, then run `python operator-proof.py` and read what it recorded.
4. Choose **Check work**.

The pool asks for two workers; the ordinary `worker` Deployment stays at zero on purpose.
Keep the owner reference and the namespaced permissions as they are.
Check work submits a job and checks the operator’s workers complete it.
