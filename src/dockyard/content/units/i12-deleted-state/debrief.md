## Compare your recovery

Both objects came back with their original UIDs, which only a restore from the snapshot can do; reapplying YAML would have made look-alikes.
Restoring into a new directory kept the old data available if the restore had gone wrong.
The revision bump and compaction made the controllers re-read everything, so the Deployment's Pods were recreated and the frontend worked again.
The database was never in etcd, so its rows were unaffected either way.

Check your understanding:
If someone had created a new Role an hour after the snapshot, what would have happened to it?
When would reapplying the YAML be a better choice than restoring etcd?
What would you have needed if the cleanup had also deleted rows in the database?
