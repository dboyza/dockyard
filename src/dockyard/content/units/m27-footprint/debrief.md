## What changed

The file-sharing service is stopped and masked, so nothing serves the node's files on port 8081 now or after a reboot.
The `backup` account can no longer log in or use `sudo`, which removes a quiet route to root on the worker.

Check your understanding: why does a service listening on `127.0.0.1` matter less than one on `0.0.0.0`, and why does it still matter a little?
Why retire the account instead of deleting it straight away?
