## What you’re walking into

A new release was published to the lab’s private registry without trouble.
Then the registry’s credentials were rotated, and now new API Pods cannot start: they are stuck pulling the image.

## How to approach an incident

1. **Describe the symptom** in one sentence, in terms a user would notice.
2. **Collect evidence** before changing anything.
3. **Form a theory** that explains all of that evidence.
4. **Make the smallest fix** that addresses the cause.
5. **Check the result** with fresh Pods and a new job.

Write each step in your notes as you go.
Hints and the reference solution are available, but using them marks this attempt as practice with help.

## Pulling from a private registry

A registry that requires a login needs Kubernetes to present credentials when a node pulls an image.
Those credentials live in a Secret of type `kubernetes.io/dockerconfigjson`, and the Pod lists it under `imagePullSecrets` (or its ServiceAccount does).
The Secret must be in the Pod’s namespace, and its entry must be for the **exact** registry address in the image name, including the port.

The standard way to create one, which you will also use in the exams, is:

```sh
kubectl create secret docker-registry NAME \
  --docker-server=REGISTRY_ADDRESS \
  --docker-username=USER \
  --docker-password="$PASSWORD_VARIABLE" \
  --dry-run=client -o yaml | kubectl apply -f -
```

Using `--dry-run=client -o yaml | kubectl apply -f -` lets you update a Secret that already exists.
Refer to the password through a variable, as shown, rather than typing it, so it never lands in your shell history or notes.

Logging in with `docker login` on your own computer does nothing for the cluster’s nodes.

## Reading pull errors

`kubectl describe pod` shows the pull error in its Events.
Read it carefully, because different problems look similar at a glance:

- the image or tag does not exist (“not found”, “manifest unknown”);
- the registry cannot be reached (connection refused or timed out);
- the registry refused the login (“unauthorized”, “authentication required”).

This lab’s registry runs on a local Docker network with plain HTTP and a password, and the cluster’s nodes are configured to reach it.
The Deployment uses `imagePullPolicy: Always`, so every new Pod checks the registry with its credentials, even if the image is already cached on the node.
