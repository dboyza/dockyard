## What changed

`catalog` was found through its behavior, its access to Dispatch's Secrets was traced to a RoleBinding and revoked, and a NetworkPolicy with no rules now cuts its Pods off completely.
The Pod itself is still running, unchanged, for whoever examines it next.

Check your understanding: why isolate instead of deleting the Pod straight away, and when would deleting be the right call?
The database password may have been read.
What else must happen before this incident is closed?
