## Resume the paused deployments

Both environments’ Flux Kustomizations are suspended, even though the repository holds a healthy declaration.

1. Look at the GitRepository, `flux.yaml`, and the `dispatch-deployer` permissions.
2. Remove the suspension in `flux.yaml`, apply it with `python render.py flux.yaml | kubectl apply -f -`, and run `python gitops.py wait`.
3. Confirm both environments applied the same commit as `git -C delivery rev-parse HEAD`.
4. Choose **Check work**.

Leave the application processing jobs, and keep the database password out of Git.
