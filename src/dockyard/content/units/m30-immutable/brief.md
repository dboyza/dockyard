## Find the changed replica and make the uploader immutable

Someone changed files inside one of the three running `uploader` replicas in `uploads`.

1. Compare the replicas, find the one whose files differ, and write its Pod name into `tampered-pod.txt`.
2. Make the uploader's root filesystem read-only and turn off privilege escalation, giving it writable volumes only for `/tmp` and `/var/cache/uploads`.
3. Roll it out, confirm root inside the container can no longer change its files, and that uploads are still cached.
4. Choose **Check work**.

Keep the uploader running as root; immutability must hold for root too.
In your notes, explain why replacing the Pods was part of the fix, not just the configuration change.
