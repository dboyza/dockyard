# Promote the same artifact and repair the source of truth

Promotion changes which environment selects an already tested digest.
Rebuilding a supposedly identical image for staging weakens that guarantee because the new build may contain different inputs.
This lab has separate development and staging Deployments in one practice namespace, sharing supplied dependencies to fit local resources.
They are separate release targets, not a production tenant-isolation design.

The supplied delivery-proof.py performs an inspectable rehearsal using ordinary Git, Docker, kubectl, and Flux operations.
It first scales the development Deployment to zero and observes Flux restore the declared count.
It then builds and tests dispatch-3, commits that digest to development, waits for readiness, and promotes exactly that digest to staging in a separate commit.
It finally commits an unavailable staging image digest, observes an actual ErrImagePull or ImagePullBackOff condition, and uses git revert to create a new recovery commit.

For a different environment, the manual rollback sequence would be:

```sh
git -C delivery log --oneline -5
git -C delivery revert --no-edit "$BAD_COMMIT"
git -C delivery push origin main
kubectl get kustomizations.kustomize.toolkit.fluxcd.io -n flux-system
```

A revert records an inverse change in a new commit while preserving history.
Resetting a live Deployment with kubectl rollout undo changes the cluster but leaves the faulty Git declaration intact, so the controller can reapply it.
Inspect the failed source commit, recovery commit, controller revision, and actual running process before calling recovery complete.

The supplied rehearsal restores Git in a finally block after introducing the bad candidate.
The existing healthy staging replica may continue serving during the failed rollout because maxUnavailable is zero.
An image-pull failure therefore establishes a failed candidate rollout, not necessarily a complete service outage.
The evidence file records that distinction through the failed Pod identity and reason.

Read delivery-proof.py before running it, then inspect delivery-evidence.json alongside git show and live Kubernetes state.
Local evidence files can be edited and are not tamper-proof certifications.
The checker additionally validates the actual commit ancestry, changed image declarations, remote branch, controller revisions, and working service.
