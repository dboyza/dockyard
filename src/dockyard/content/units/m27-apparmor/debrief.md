## What changed

Both nodes have `dockyard-processor` loaded in enforce mode and installed for the next boot.
The processor runs under it.
It keeps writing results in `/data`, but even as root it can no longer write to `/etc` or anywhere else the profile does not allow.

Check your understanding.
Imagine a processor Pod is rescheduled onto a newly added node that has never loaded the profile.
What would happen, and why is that the safer behavior?
When would you use complain mode, and why should a profile not stay in it?
