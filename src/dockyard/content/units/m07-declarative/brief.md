## Update an old manifest and apply it

The cluster runs one Dispatch replica.
Your workspace has a `deployment.yaml` that asks for two replicas, but it was written for the retired `extensions/v1beta1` API.

1. Confirm which context and namespace you are using.
2. Try a server dry run of the file and read the error.
3. Update the file to the current Deployment API, keeping its selector matching the Pod labels.
4. Look at the diff, apply it with `sh run.sh`, and wait for both replicas to be ready.
5. Write a short `CHANGE.md` explaining why switching namespace or context would not have fixed the original error.
6. Choose **Check work**.

Check work tests the running Deployment and that the file in your workspace uses a supported API version.
