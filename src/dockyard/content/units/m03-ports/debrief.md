## What did the mapping change?

The application still listens on port 8080.
Your repair changed where Docker forwards an incoming request, not the application’s own setting.

Read the repaired mapping aloud from left to right.
Then explain why `127.0.0.1` inside the container and `127.0.0.1` in your terminal refer to different places.
You’ll need that distinction when Dispatch calls another container.
