## Declared, accepted, and running

Your updated file described what you wanted, the cluster accepted it, and the Deployment controller made it true.
Those are three separate steps, and each can fail on its own.

Check your understanding:
What happens to the cluster if you edit `deployment.yaml` but never apply it?
Why is it dangerous to apply a file without first checking your current context?
Try generating a Deployment with `kubectl create deployment ... --dry-run=client -o yaml` and compare it with `deployment.yaml`.
