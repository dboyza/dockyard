## What changed

The release is signed by your key, production runs exactly the digest you verified, and the cluster refuses anything in `production` that is not pinned to the release registry.
A moved tag or a laptop build can no longer reach production unnoticed.

Check your understanding: an attacker pushes a different image to the release registry and gives you its digest.
Would your policy admit it, and what would stop it in a fully configured cluster?
Why sign the digest rather than the tag?
