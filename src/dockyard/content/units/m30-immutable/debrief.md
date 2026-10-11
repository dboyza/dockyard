## What changed

The tampered replica is gone, replaced with the other Pods by a rollout from the unchanged image.
Every uploader now runs with a read-only root filesystem and no privilege escalation, writing only to two short-lived volumes, so even root inside it cannot plant a program again.

Check your understanding: an attacker gets into an immutable uploader.
What can they still change, and what disappears when the Pod is replaced?
Why are files in an `emptyDir` volume less worrying than files in the image's folders?
