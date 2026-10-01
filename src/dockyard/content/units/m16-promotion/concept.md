## Promote what you tested, and roll back through Git

**Promotion** means moving a release from one environment to the next, for example from development to staging.
The safe way is to promote the *exact same image*, by digest, that passed testing in the earlier environment.
Rebuilding it for staging would create a new image that might differ in ways nobody tested.

In this lab, development and staging are two separate Deployments in one namespace, sharing the database and queue to save resources.
That is a practice shortcut, not how you would separate real environments.

## The rehearsal

The supplied `delivery-proof.py` walks through a whole release cycle using ordinary Git, Docker, kubectl, and Flux commands.
Read it before running it. It:

1. Scales the development Deployment to zero by hand, and watches Flux restore it from Git.
2. Builds and tests release `dispatch-3`, commits its digest for development, and waits for it to be ready.
3. Promotes that same digest to staging in a separate commit.
4. Commits a staging image that does not exist, watches the rollout fail with `ErrImagePull` or `ImagePullBackOff`, then recovers with `git revert`.

It puts Git back in order even if a step fails, and saves what happened in `delivery-evidence.json`.

```figure
promotion-flow
```

## Rolling back the GitOps way

```sh
git -C delivery log --oneline -5
git -C delivery revert --no-edit "$BAD_COMMIT"
git -C delivery push origin main
kubectl get kustomizations.kustomize.toolkit.fluxcd.io -n flux-system
```

`git revert` makes a *new* commit that undoes an earlier one, so history keeps both the mistake and the fix.
With GitOps, `kubectl rollout undo` is only temporary: Git still declares the bad version, and Flux will apply it again on its next pass.
Always fix the declaration in Git.

Because staging’s rolling update keeps `maxUnavailable: 0`, its existing healthy Pod keeps serving while the bad candidate fails to pull.
So a failed pull here means a failed rollout, not necessarily an outage; the evidence file records which Pod failed and why.

## Checking the result yourself

Do not take the script’s last message as the result.
Look at each commit with `git -C delivery show`, the controllers’ applied revisions, and the running Pods’ images.
The evidence file is a local record anyone could edit; Check work verifies the real commit history, the remote branch, Flux’s status, and the running service.
