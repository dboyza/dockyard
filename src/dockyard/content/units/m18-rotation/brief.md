## Rotate the database password

1. Read `rotate.py` to see the order it changes things in.
2. Run `python rotate.py`, then wait for the `dispatch` and `worker` rollouts.
3. Choose **Check work**.

Check work logs in with the new password, confirms the old one is rejected by the same running database, and completes a job.
Do not re-apply the original bootstrap Secret afterwards; that would put the old password back in the cluster.
