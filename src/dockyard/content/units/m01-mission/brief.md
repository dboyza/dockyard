## Get Dispatch running again

Prepare lab gives you a container whose program has already finished with exit code zero.
The supplied app.py is correct and does not need editing.

Restore a long-running Dispatch API using the assigned container name, lab label, and host port.
The endpoint must bind only to 127.0.0.1 and respond on `/healthz` with service `dispatch`.
Preserve other containers and the supplied image.
Leave the corrected instance running.

In your notes, answer three questions: What command did the broken container run?
Why did it finish instead of serving requests?
Which two observations show that your replacement works?
These answers are for self-review; the checker tests the repaired service, not your explanation.
Use only commands and concepts already introduced in this module.
