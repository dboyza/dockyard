## Let new Pods pull the release again

Find out why new API Pods cannot pull the image, and fix it.

- The registry address is in `registry.txt`. The username is `learner`, and the current password is in the `DOCKYARD_REGISTRY_PASSWORD` variable. Refer to the variable; do not type or copy the password itself.
- Keep the registry’s authentication on, and keep the published `dispatch:incident` release.
- Get two ready API replicas with `imagePullPolicy: Always`, and complete a new job.
- Keep the namespace, the database’s storage, and its stored job.

Loading the image onto the nodes directly, turning off authentication, or switching to a non-registry image does not count.
In your notes, record how you told apart a missing image, an unreachable registry, and a rejected login.
