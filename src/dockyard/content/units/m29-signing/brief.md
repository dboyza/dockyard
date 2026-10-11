## Sign the release and admit only what you verified

Production runs a Dispatch image nobody can account for, and nothing stops more of the same.

1. Generate a cosign key pair, then sign and verify the release in the lab registry by its digest.
2. Deploy production's Dispatch from that exact digest, using `production.yaml` and `sh run.sh`.
3. Add a ValidatingAdmissionPolicy, bound to `production` with `Deny`, that admits only images from the release registry pinned by digest.
4. Confirm an image from anywhere else is refused, and choose **Check work**.

Keep `cosign.pub` in your workspace; Dockyard verifies the signature with it.
In your notes, explain what your admission policy guarantees, and what it does not.
