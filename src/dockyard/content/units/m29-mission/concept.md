## Ship a release you can vouch for

Dispatch 2.0 is ready to go to production, and this time the security team wants evidence at every step: what is in the image, what the manifest allows, who released it, and what the cluster will accept.
Building that release is your job.

Use what this module taught: a minimal image, static analysis of the manifest that is actually deployed, signing by digest, and an admission rule for production.
The registry address is in `registry.txt`; `docker push` publishes to it, and `docker inspect --format '{{index .RepoDigests 0}}'` shows the pushed image's digest reference.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
Check work tests the live cluster; your report is for your own review against `report-rubric.md`.
