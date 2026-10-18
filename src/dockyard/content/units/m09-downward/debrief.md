## What changed

Each Dispatch Pod now reports its own identity, because Kubernetes filled in `fieldRef` and `resourceFieldRef` separately for each Pod as it was created.
A fixed `value` is part of the template, so every replica received the same text.
The labels arrive as a file because labels can change while a Pod runs.
The kubelet keeps that file current.
An environment variable is fixed when the container starts.

Check your understanding: if you added a label to one running Pod with `kubectl label`, which would show it, the labels file or an environment variable, and roughly when?
Why does a memory limit of 192Mi appear as `201326592`?
