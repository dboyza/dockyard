## Confine the document processor with AppArmor

The processor in `processing` parses untrusted files as root, with no AppArmor profile.

1. Confirm it can write to `/etc` inside its container.
2. Install and load the supplied `dockyard-processor` profile on both nodes, so it also survives a reboot.
3. Apply the profile to the processor container in `processing.yaml`, and roll it out.
4. Confirm the container reports `dockyard-processor (enforce)`, cannot write to `/etc`, and still processes documents, then choose **Check work**.

Keep the processor running as root; the point is that AppArmor confines root too.
In your notes, explain why the profile has to be loaded on every node and not only the one the Pod is running on now.
