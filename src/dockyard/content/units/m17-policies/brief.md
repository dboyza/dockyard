## Make the memory-limit rule actually refuse

The platform requires a memory limit on every container in `dispatch`, but limitless Deployments are still being accepted.

1. Test the rule with `kubectl create deployment probe --image=busybox --dry-run=server` in `dispatch` and in `sandbox`.
2. Find why `policy.yaml`'s binding refuses nothing.
3. Make the binding deny violations, and apply it only to the `dispatch` namespace.
4. Run `sh run.sh`, repeat both dry runs, and choose **Check work**.

Keep the policy's rule as it is, and leave `sandbox` free to skip limits.
In your notes, explain the difference between the policy and its binding.
