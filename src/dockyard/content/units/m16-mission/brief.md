## Hand over a working, reversible delivery process

1. Turn the pipeline’s test gate back on and publish a tested release.
2. Resume both environments in Flux and confirm they apply the current commit and become Ready.
3. Show Flux repairing manual drift, the same `dispatch-3` digest promoted to staging, a real failed pull of a bad candidate, and recovery with a new `git revert` commit.
4. Choose **Check work**.

Keep the deployer’s permissions limited to Dispatch Deployments, and keep the database password out of Git.

Write `DELIVERY-NOTES.md` explaining the chain of evidence from test to running Pod, what users actually experienced during the failed candidate, and how someone would repeat or reverse a release.
