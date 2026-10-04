## Get inside two Pods that will not let you in

The workers crash straight after starting, and the platform team wants to see what runs inside an API container without restarting it.

1. Find which file the worker could not open, then explore a debugging copy of a worker Pod to find the real entry point.
2. Correct the command in `worker.yaml` and run `sh run.sh`.
3. Attach an ephemeral container that targets `api` in one API Pod, run `ps`, and save its output as `api-processes.txt`.
4. Delete the debugging copy, then choose **Check work**.

Do not change the API Deployment; replacing its Pods would remove the ephemeral container you attached.
In your notes, explain why `kubectl exec` could not help with the workers.
