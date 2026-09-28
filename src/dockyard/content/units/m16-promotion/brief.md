## Rehearse a promotion and a recovery

The current release is healthy, but no promotion or recovery has happened yet.

1. Read `delivery-proof.py`.
2. Run `python gitops.py wait`, then `python delivery-proof.py`.
3. Inspect each new commit with `git -C delivery log` and `git -C delivery show`, and compare with the running Pods.
4. Choose **Check work**.

In your notes, explain why the same digest reached staging, why Flux undid the manual scale-down, and why recovery used `git revert` rather than `kubectl rollout undo`.
Leave `dispatch-3` serving in both environments, with the failed candidate and its revert kept in history.
