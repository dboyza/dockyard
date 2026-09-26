# Repair a Pod's local preparation contract

The worker's init command exits unsuccessfully before writing its configuration.
Its observer also mounts a different emptyDir than the worker, so repairing only the init command still leaves a misleading view.

1. Observe init status and logs before editing `worker.yaml`.
2. Make init container `configure` write `queue=redis://queue:6379/0` into `/shared/worker.conf` and exit successfully.
3. Mount the same `shared` emptyDir into the worker and `observer` containers at `/shared`.
4. Apply and wait for two available worker replicas.
5. Confirm both containers read the same file, then verify real job processing.

Keep the helper containers in each worker Pod; moving the observer to a standalone Pod would remove the required shared lifecycle and storage behavior.
