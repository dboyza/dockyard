## Compare your diagnosis

The maintenance left `jobs.db` owned by user 10001, but without its owner’s write permission.
Reading still worked, so health checks and the job list looked normal; only saving failed.
Giving the owner write permission back fixed it without widening access or touching the data.

Check your understanding:
Which observation showed the problem was writing rather than reading?
Why would `chmod 777` or running as root be a worse fix, even though either would make saving work?
What check could a team run regularly to catch this, beyond `/healthz`?
