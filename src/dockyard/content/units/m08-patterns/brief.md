## Fix the worker Pods’ preparation

1. Find out why the worker Pods never start, using their status and the `configure` container’s logs.
2. Make `configure` write `queue=redis://queue:6379/0` into `/shared/worker.conf` and exit successfully.
3. Make `worker` and `observer` both mount the `shared` volume at `/shared`.
4. Apply `worker.yaml` and wait for two ready worker Pods.
5. Confirm the worker and the observer see the same file, then check a job is processed.
6. Choose **Check work**.

Keep all three containers in the worker Pods; moving the observer into its own Pod would stop it sharing the folder.
