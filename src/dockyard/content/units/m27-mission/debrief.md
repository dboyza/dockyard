## What changed

The control plane no longer serves its logs to the network or keeps a contractor account with root-equivalent access.
The renderer still runs as root and still produces pages, but AppArmor limits its writes to its output and temporary files, and seccomp filters its system calls.

Check your understanding: which of your changes would still protect the cluster if an attacker found a bug in the renderer's template parser, and which would not matter to that attacker?
What would you ask the renderer's vendor for, and why?
