## What changed

The worker's containerd now knows a `runsc` handler, the `gvisor` RuntimeClass names it, and its node selector keeps sandboxed Pods on the node that has it.
`template-preview` runs inside gVisor: its system calls go to gVisor's own kernel, which shields the node's kernel from whatever the uploaded code tries.

Check your understanding: what would happen to `template-preview` if the worker were drained and only the control-plane node remained?
Why not run every workload under gVisor?
