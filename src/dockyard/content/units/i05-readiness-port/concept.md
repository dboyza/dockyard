## What you’re walking into

After someone tidied up the port names in the API’s Deployment, both API Pods finish starting and answer health requests if you ask them directly.
But they never become Ready, so the `dispatch` Service has no usable endpoints and nobody can submit jobs.

## How to approach an incident

1. **Describe the symptom** in one sentence, in terms a user would notice.
2. **Collect evidence** before changing anything.
3. **Form a theory** that explains all of that evidence.
4. **Make the smallest fix** that addresses the cause.
5. **Check the result** the way a user would, with a new job through the Service.

Write each step in your notes as you go.
Hints and the reference solution are available, but using them marks this attempt as practice with help.

## Useful reminders

A probe’s `port` can be a number or the **name** of one of the container’s ports, such as `port: http`.
A name is looked up in that container’s own `ports` list, not in the Service.
If the name points at a port nothing listens on, the probe fails even though the application is fine.

`kubectl describe pod` shows each probe’s target and recent failures in its Events.
A “connection refused” error means nothing was listening at that port, which is different from the application answering that it is not ready.

`kubectl get endpointslices` lists every selected Pod’s address, including Pods that are not ready.
Use `kubectl describe endpointslice NAME` to see each address’s `Ready` condition.
