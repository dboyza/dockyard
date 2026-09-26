## Build a deliberate runtime boundary

Create a multi-stage Dockerfile using the supplied BASE_IMAGE argument for both stages.
In the first stage, copy app.py and VERSION into `/source` and validate app.py with `python -m py_compile`.
In the final stage, copy only app.py and VERSION into `/app`, give them suitable ownership, and set a non-root runtime user.
The final container must not contain `/source` and must not mount the host workspace.

Build and start the assigned image and container using the earlier label and loopback port contract.
Leave release `dispatch-1` responding successfully.
The live checker verifies runtime identity and file boundaries; review your Dockerfile to explain the two stages and the compile step.
