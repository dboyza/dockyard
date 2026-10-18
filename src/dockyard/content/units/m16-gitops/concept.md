## Git as the source of truth

**GitOps** means the desired state of your cluster lives in a Git repository, and a controller keeps the cluster matching it.
To change what runs, you commit to Git; the controller notices and applies it.
Manual changes to the cluster are undone on the controller’s next pass, the same reconciliation idea you have seen throughout Kubernetes.

```figure
gitops-loop
```

This lab runs a real local Git server and **Flux**, a popular GitOps controller.
Nothing is sent to an external Git host.
The practice repository is the `delivery` folder in your workspace, with its own local author settings; your own Git configuration is untouched.

## Two Flux objects

- A **GitRepository** tells Flux where to fetch from and how often.
- A Flux **Kustomization** tells Flux which folder of that repository to build and apply, and how often.
  It also says whether to **prune**, which means deleting objects that were removed from Git.

The Flux Kustomization is a cluster object; the `kustomization.yaml` file inside the repository is an ordinary Kustomize build file.
The names are similar, but they are different things.

```sh
git -C delivery log --oneline --decorate
kubectl get gitrepositories -n flux-system
kubectl get kustomizations.kustomize.toolkit.fluxcd.io -n flux-system
kubectl describe kustomization.kustomize.toolkit.fluxcd.io development -n flux-system
```

`git -C delivery` runs Git inside the `delivery` folder.

## Reading Flux’s status

Several things can go wrong separately, so check each:

- Did the GitRepository fetch the latest commit?
- Did the Kustomization build and apply that commit? Compare its `lastAppliedRevision` with `git -C delivery rev-parse HEAD`.
- Is it `Ready`, with a current `observedGeneration`?
- Is the application itself working?

A folder that does not exist fails at the build step even though fetching worked.
A folder containing a broken Deployment can apply successfully and still fail its health check.

Setting `suspend: true` on a Kustomization pauses it: nothing new is applied, and nothing already running is deleted.

The supplied `python gitops.py wait` waits until both environments have applied the current commit and report Ready.
It only waits; it does not fix anything.

## Limiting what Flux can do

Flux applies your application’s manifests as a ServiceAccount called `dispatch-deployer` (set by `serviceAccountName`), which may only manage Deployments in `dispatch` and read the Pods and ReplicaSets they create.
It cannot read Secrets through the API or touch `kube-system`.
Anyone who can push to the repository can still deploy code that runs in that namespace, so write access to the repository is effectively deployment access.
The database password is created separately and never committed.
