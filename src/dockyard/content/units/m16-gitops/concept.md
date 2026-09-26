# Git declares intent; controllers reconcile it

GitOps uses a versioned source as the desired state and a controller that repeatedly compares it with the cluster.
The local smart HTTP Git server and Flux source-controller and kustomize-controller are real services.
There is no external Git account or hosted automation.
The practice repository lives in delivery and has its own local author identity.
Its configuration does not alter your normal repositories or global Git settings.

A GitRepository resource tells Flux where to fetch a branch and how often to inspect it.
A Flux Kustomization tells another controller which directory to build, where to apply it, and whether to prune previously managed resources removed from that directory.
The file named kustomization.yaml inside the repository is the Kustomize build definition; the similarly named Flux API resource controls reconciliation.
They are separate objects with different jobs.

```sh
git -C delivery log --oneline --decorate
kubectl get gitrepositories -n flux-system
kubectl get kustomizations.kustomize.toolkit.fluxcd.io -n flux-system
kubectl describe kustomization.kustomize.toolkit.fluxcd.io development -n flux-system
```

For example, an unrelated documentation environment could reference ./environments/documentation with interval: 30s, prune: true, and wait: true.
A missing path fails the build step even when Git fetching succeeds.
A valid path containing an unhealthy Deployment can be applied successfully while its health check still fails.
Inspect source artifact revision, lastAppliedRevision, Ready condition, and live workload behavior separately.

Suspending a Kustomization pauses its reconciliation without deleting the current resources.
Changing a live Deployment while reconciliation is active is temporary drift; change the Git source for a durable update.
The supplied gitops.py wait helper waits for both environments to report the current local commit and a current-generation Ready condition.
It does not make the commit or controller healthy by itself.

The controller installation has cluster-level infrastructure permissions inside this disposable cluster.
For the learner's releases, serviceAccountName: dispatch-deployer makes Flux impersonate a narrowly scoped identity that can manage Deployments only in dispatch.
Read-only Pod and ReplicaSet access lets the health check follow the Deployment without granting write access to those resources.
That account cannot directly read Secrets through the API or edit kube-system workloads.
Deployment authors can still mount namespace Secrets or run code, so this is not a boundary against an untrusted manifest author.
Source files contain image references and deployment intent; the database credential is provisioned separately and never committed to the practice repository.
