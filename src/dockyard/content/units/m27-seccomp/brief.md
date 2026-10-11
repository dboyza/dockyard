## Give both processing containers a seccomp filter

Neither container in `processing` has a seccomp filter: the processor's was turned off while debugging, and `intake` never had one.

1. Confirm both report `Seccomp: 0`.
2. Install the supplied `profiles/no-chmod.json` on both nodes where the kubelet looks for Localhost profiles.
3. Apply it to the processor, give `intake` the runtime's default profile, and roll both out.
4. Confirm both report `Seccomp: 2`, the processor can no longer change file permissions, and it still processes documents, then choose **Check work**.

In your notes, explain why a profile that only lists calls to refuse is weaker than one that lists calls to allow.
