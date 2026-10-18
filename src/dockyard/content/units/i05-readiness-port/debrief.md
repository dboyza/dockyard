## Compare your diagnosis

The startup probe passed, so Dispatch had started.
The readiness probe used a port name that now pointed at a port where nothing listened.
Every readiness check got “connection refused”, so the Pods were never added to the Service.
Pointing readiness back at the real listener on 8080 fixed it while keeping the database check in place.

Check your understanding:
Which observation ruled out slow startup, and which ruled out a database problem?
Why were the Pods not restarted, even though readiness kept failing?
