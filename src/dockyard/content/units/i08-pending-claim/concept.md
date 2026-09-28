## What you’re walking into

A new `archiver` Deployment was rolled out to store archive files on a new claim called `archive`.
It never started, and the claim has been `Pending` ever since.
The storage provisioner is running, and the rest of Dispatch works normally.

## How to approach an incident

1. **Describe the symptom** in one sentence, in terms a user would notice.
2. **Collect evidence** before changing anything.
3. **Form a theory** that explains all of that evidence.
4. **Make the smallest fix** that addresses the cause.
5. **Check the result** by writing a file and reading it back.

Write each step in your notes as you go.
Hints and the reference solution are available, but using them marks this attempt as practice with help.

## Useful reminders

`Pending` tells you something has not finished; it does not tell you why.
The `standard` class waits for the first Pod that uses a claim to be scheduled before creating storage, so a claim can be Pending simply because its Pod cannot be scheduled.
A Pod’s `nodeSelector` says which node labels it requires.
If no node has those labels, the Pod stays Pending, and so does its claim.

Read the events on both the claim and the Pod, and compare the Pod’s requirements with `kubectl get nodes --show-labels`.
Change a placement rule only to a node that genuinely suits the workload: this lab’s nodes offer a `warm` storage tier that is appropriate for archives.
