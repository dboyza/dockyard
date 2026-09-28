## Separate starting from being ready

Your dependency conditions now wait for real health checks.
Your completed job tests the application after those checks succeed.

Predict what happens if PostgreSQL becomes unavailable five minutes after startup.
Which part can Compose’s startup ordering handle, and which part must the application handle?
