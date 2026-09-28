## Restore the backup onto separate storage

The original database has been stopped, with its storage kept.

1. Read `restore.py`.
2. Run `python restore.py`.
3. Check the new StatefulSet and claim, and that the `db` Service now selects the restored database.
4. Choose **Check work**.

Keep the original claim untouched.
Check work decrypts the real backup, confirms a tampered copy is rejected, checks the two databases use different storage, and reads the known record through the frontend.
