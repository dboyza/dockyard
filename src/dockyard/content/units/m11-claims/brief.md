## Put the database on persistent storage

The claim `dispatch-data` exists, but the database Deployment still uses `emptyDir`.

1. Look at the claim with `kubectl describe pvc dispatch-data` and explain in your notes why it may be Pending.
2. In `platform.yaml`, change the database’s `data` volume to use claim `dispatch-data`, and set its update strategy to `Recreate`. Keep the mount path `/var/lib/postgresql/data` and one replica.
3. Apply `claim.yaml`, then run `sh run.sh`, and wait for the database to be ready.
4. Run `python storage-proof.py` and confirm the replacement Pod read the original marker.
5. Choose **Check work**.

There is no existing data to move here.
In a real migration, back up the data first: attaching an empty new volume does not copy anything across.
