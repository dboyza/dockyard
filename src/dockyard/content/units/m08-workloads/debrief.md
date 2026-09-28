## Two controllers, two different fixes

The Deployment needed more copies; the DaemonSet needed permission to run somewhere.
Scaling a DaemonSet is not possible, because its size comes from the nodes it matches.

Check your understanding:
If the workers had the wrong Redis address, why would adding more workers not help, and which log would show it?
Which controller would you choose for a database migration that must run once per release?
