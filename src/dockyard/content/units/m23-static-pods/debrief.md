## What you did

You found two separate faults below the API: a stopped kubelet and a static Pod manifest in the wrong place.
With the file back and the kubelet running, the kubelet started the scheduler from its manifest, with no Deployment or controller involved.
A new Pod getting a node showed the scheduler was really working, which old running Pods could never show.

## Check your understanding

- Which command showed you the scheduler's file was missing, and which showed the kubelet was stopped?
- Why does deleting a control-plane Pod with kubectl not restart it the way you might expect?
- How would you run your own static Pod on a worker node?

## Beyond this lab

When the API is down, the node's own tools, `systemctl`, `journalctl`, `crictl`, and the manifest files, are what you have left.
Make sure you can always reach your control-plane nodes directly.
