## Rules at the door, limits inside

Admission now refuses Pods that would escalate privileges, and the running API process really is non-root, capability-free, filtered, and unable to change its own files.

Check your understanding:
Why was changing the namespace label not enough on its own?
Name one restriction that Restricted requires, and one that is extra hardening you chose to add.
