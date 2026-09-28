## The security capstone

Several problems have happened at once, and each needs a different fix:

- the image still contains the unused vulnerable library;
- the database is still on its original password;
- the primary database has stopped (an encrypted backup was taken beforehand);
- someone edited the frontend’s network policy directly in the cluster, and it now names a client label that has been retired. The file in your workspace was not changed.

Some of these produce the same symptom, such as “the dashboard does not work”.
Look at the evidence (Pods, the Service’s selector, the policy’s peers, the backup’s details) before deciding which to fix first, and in what order.
Keep the original database storage until the restored one is verified.

You are done when:

- the library is gone from the image and the running processes;
- the new password works and the old one is rejected;
- the restored database, on separate storage, is serving;
- a new job from the frontend completes.

Keep your before and after scan reports; they record the database date.
Passing this mission does not make the remaining image findings safe or replace a real security review.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
