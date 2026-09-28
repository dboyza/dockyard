## What you’re walking into

A release changed some labels.
Since then, both Dispatch API Pods are running and ready, and you can reach each one directly by its IP, but requests to the `dispatch` Service fail to connect.

## How to approach an incident

1. **Describe the symptom** in one sentence, in terms a user would notice.
2. **Collect evidence** before changing anything.
3. **Form a theory** that explains all of that evidence.
4. **Make the smallest fix** that addresses the cause.
5. **Check the result** the way a user would, with a new job through the Service.

Write each step in your notes as you go.
Hints and the reference solution are available, but using them marks this attempt as practice with help.

## Useful reminders

A Service’s name can resolve perfectly while it has no Pods behind it.
Its EndpointSlices show which Pods it has actually selected.
A selector with several labels only matches Pods that have **all** of them: a Service selecting `app: catalog` and `tier: public` ignores a Pod labelled only `app: catalog`.

The Service was changed directly in the cluster, not through a workspace file.
You can change it the same way, with `kubectl edit service dispatch`.
