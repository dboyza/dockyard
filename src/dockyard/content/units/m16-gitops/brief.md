# Resume a declared release

Both environment Kustomizations are suspended even though the practice repository contains a healthy declaration.
Inspect the GitRepository source, flux.yaml, and the scoped deployer permissions.
Repair the suspend fields in flux.yaml, render and apply that file, and run python gitops.py wait.
Confirm both applied revisions match git -C delivery rev-parse HEAD and the remote main branch.
Leave the live application processing jobs and keep database credentials out of Git.
