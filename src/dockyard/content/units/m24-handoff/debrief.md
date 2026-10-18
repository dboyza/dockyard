## What you did

The new image did not exist, so the new Pod could never start, while the old Pods kept serving.
Health checks alone would have said everything was fine; the Deployment's counts and `rollout status` showed the release had not finished.
Rolling back, or setting a working image, let the rollout complete, and a new job showed the API was useful again.

## Check your understanding

- Which column in `kubectl get deployment` first showed that the release had not finished?
- What would have happened with `maxUnavailable: 1` instead of `0`?
- Could someone use your handoff alone to repeat your checks and recognize when to roll back?

## Beyond this lab

Most teams set `progressDeadlineSeconds` and alert when a Deployment reports `Progressing=False`, so a stuck release is noticed without anyone watching a terminal.
