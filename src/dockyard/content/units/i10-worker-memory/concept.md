## What you’re walking into

Someone changed the workers’ memory settings.
Since then the workers keep restarting.
The API still accepts jobs, but no results come back.

## How to approach an incident

1. **Describe the symptom** in one sentence, in terms a user would notice.
2. **Collect evidence** before changing anything.
3. **Form a theory** that explains all of that evidence.
4. **Make the smallest fix** that addresses the cause.
5. **Check the result** the way a user would, with a new job.

Write each step in your notes as you go.
Hints and the reference solution are available, but using them marks this attempt as practice with help.

## Useful reminders

A container can restart because its process exited, because it failed a liveness probe, or because it used more memory than its limit.
Each needs a different fix, so find out which it was first.
`kubectl describe pod` shows a container’s **Last State**, including its **Reason**; `OOMKilled` means it went over its memory limit.

```sh
kubectl get pods -l app=worker
kubectl describe pod POD_NAME | grep -A5 "Last State"
```

A memory **request** only affects scheduling; the **limit** is what the container is killed for exceeding.
The worker in this lab deliberately keeps an 80 MiB working set in memory, on top of what Python itself needs.
Pick a limit with room for all of that.
