## Data that outlives the Pod

PostgreSQL now writes through the claim to a PersistentVolume, and a brand-new Pod found the marker the old one wrote.

Check your understanding:
Trace the data from `/var/lib/postgresql/data` to the node’s disk, naming each object in the chain.
Which of those objects changed when the Pod was replaced, and which stayed the same?
What would you need to create by hand if the cluster had no provisioner?
