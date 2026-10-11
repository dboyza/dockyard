## What changed

The Dispatch image now runs as a non-root user, starts Python directly, and contains no shell, no package manager, and no setuid programs.
An attacker who gets code running inside it has far fewer tools to work with, and there are fewer packages to patch.

Check your understanding: why does deleting a tool in a later step not shrink the image's download size, and how would a multi-stage build fix that?
What would you lose for debugging, and how does `kubectl debug` with an ephemeral container give it back?
