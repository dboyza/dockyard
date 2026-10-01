## What you repaired

The original container published your assigned port to port 80 inside the container, but the web server was listening on port 8000.
Docker forwarded every request to a port where nothing was listening, so the container looked healthy while the page never loaded.
Its folder was also mounted with write access, which the team did not want.

Neither problem could be fixed by restarting, because ports and mounts are set when a container is created.
Replacing the container with corrected settings was the right repair.

Check your understanding:
Which command showed you the mismatch most clearly?
If the server had listened on port 80 but the page still failed, what would you have looked at next?

You have finished the foundations.
In the next module you’ll meet Dispatch, the application you’ll work on for the rest of the course, and run its first version using the same skills.
