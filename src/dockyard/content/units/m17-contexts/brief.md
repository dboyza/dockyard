## Enforce Restricted and restrict the API

The namespace only enforces Baseline, and the API allows privilege escalation, keeps the `CHOWN` capability, and has a writable root filesystem.

1. In `admission.yaml`, make the namespace enforce `restricted` (keeping the pinned version).
2. In `platform.yaml`, fix the API’s security context: no privilege escalation, all capabilities dropped, and a read-only root filesystem. Do not change how Dispatch itself works.
3. Apply both files and wait for the API rollout; the new label alone does not replace running Pods.
4. Choose **Check work**.

Keep the existing writable volumes and non-root users for the database and queue.
