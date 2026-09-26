# One owner for each environment and each desired field

Development is rendered from the Kustomize overlay in namespace dispatch.
Staging is installed from the local Helm chart in namespace staging.
The development WorkerPool controller owns its generated worker Deployment.
These ownership boundaries keep packaging tools from overwriting one another's resources.

The development overlay currently requests the wrong count and environment.
The staging release has a bad zero-replica revision, and the supplied WorkerPool controller is stopped.
Repair source intent, recover the actual release, and prove that controller reconciliation resumes.
All three systems must converge to their intended observable behavior.
A rendered manifest, a release marked deployed, or an existing CRD alone is insufficient evidence.
