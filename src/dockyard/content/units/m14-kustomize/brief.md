## Fix the development overlay

The development overlay sets Dispatch to zero replicas and patches its environment to `broken`.

1. Render the development overlay and compare it with the base.
2. Fix only `kustomize/overlays/development/kustomization.yaml`: two API replicas and environment `development`. Keep namespace `dispatch`, and leave the base alone.
3. Render and apply it with the command from Understand, then restart the API and wait for the rollout.
4. Check the Deployment, the ConfigMap, and Dispatch’s own `/config` response.
5. Choose **Check work**.

Render the staging overlay too, to compare, but do not apply it.
