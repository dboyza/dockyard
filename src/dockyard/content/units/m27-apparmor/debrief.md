## What changed

Both nodes have `dockyard-processor` loaded in enforce mode and installed for the next boot.
The processor runs under it: it keeps writing results in `/data`, but even as root it can no longer write to `/etc` or anywhere else the profile does not allow.

Check your understanding: what would happen to a processor Pod rescheduled onto a newly added node that has never loaded the profile, and why is that the safer behavior?
When would you use complain mode, and why should a profile not stay in it?
