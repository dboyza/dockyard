## Give each investigation a decision

Start with the user-visible symptom and write one sentence describing the required outcome.
For Dispatch, a successful job submission is insufficient: the worker must finish it and PostgreSQL must retain its result.
A healthy API process is an earlier boundary in that sequence.
Use a short investigation window, inspect one dependency at a time, and record what your next observation can distinguish.
A timer supports prioritization; it does not make a guessed repair safer.

A useful opening loop is: observe a symptom, state a hypothesis, choose a discriminating test, make one bounded change, and verify its effect.
If the evidence contradicts the hypothesis, update it instead of stacking more speculative changes.
Preserve enough before-change evidence to explain both cause and recovery.

## Worked example: a ready process behind an empty route

```sh
kubectl get deployment dispatch worker
kubectl get service dispatch -o yaml
kubectl get endpointslices -l kubernetes.io/service-name=dispatch
kubectl get pods -l app=dispatch --show-labels
```

Compare the Service selector with actual Pod labels before changing the application.
A Service with no eligible endpoints cannot route useful requests even if each API Pod is healthy.
After restoring that route, submit a new job and follow its status.
If it remains queued, check worker replicas and logs separately.
The first repair may reveal a second fault that the original symptom concealed.

This fixture has a Service selecting the retired track and a worker Deployment scaled to zero.
The original manifests describe the intended stable track and a running worker.
Use them as evidence while making focused repairs; wholesale bootstrap is unnecessary and can overwrite unrelated changes in real incidents.
The database and queue do not require deletion or replacement.

## Close the loop

Prove a new job reaches done, verify its computed result and persisted row, and confirm the pre-incident row still exists.
Record which observation established each boundary.
The assessment executes that real transaction from both the private browser path and the trusted cross-node frontend.
It does not infer completion from a replica count alone.

For timed practice, flag uncertain work and return after resolving well-understood tasks.
Keep context and namespace visible in the real terminal, read each task's preservation constraints, and reserve a final verification window.
Time management is useful only when the resulting state meets the requested outcome.
