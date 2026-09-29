## Three infrastructure faults at once

After some maintenance, Dispatch stopped completing jobs.
The VMs are still there, but three things no longer match the intended design:

- how the trusted frontend resolves names;
- a Linux networking setting on the worker;
- where the database is placed relative to its storage.

The design you need to restore:

- The trusted frontend runs on the control plane and uses cluster DNS.
- The API and database run on the worker, where the CSI driver can mount the original volume.
- The worker forwards Pod traffic through its network stack. On Linux, that needs the setting `net.ipv4.ip_forward` to be `1`.

Test each layer separately and fix only what the evidence points to, rather than repeating every fix from the lessons.
Keep the original database volume and its data.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
Write your handoff without credentials or administrator kubeconfigs.
