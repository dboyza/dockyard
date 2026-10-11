## Run untrusted code in a gVisor sandbox

`template-preview` in the `untrusted` namespace runs code customers upload, directly on the node's kernel.

1. Register gVisor's `runsc` handler in containerd's configuration on the worker, and restart containerd.
2. Label the worker `sandbox.dockyard.io/gvisor=true`, and create a RuntimeClass named `gvisor` for the `runsc` handler that schedules only onto labelled nodes.
3. Run `template-preview` with that RuntimeClass, and confirm from inside it that gVisor is handling its system calls.
4. Make sure the preview service still answers, and choose **Check work**.

In your notes, explain why the RuntimeClass needs a node selector in this cluster, and what gVisor costs compared with an ordinary container.
