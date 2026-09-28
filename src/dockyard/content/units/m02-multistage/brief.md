## Build, check, and run in separate stages

The supplied `app.py` and `VERSION` are ready to use.
Edit the existing Dockerfile rather than changing the application.

1. Keep the `BASE_IMAGE` argument and use it in both stages.
2. In a named first stage, copy `app.py` and `VERSION` into `/source` and run `python -m py_compile app.py`.
3. Begin a fresh final stage, copy only those two application files into `/app`, and make them readable by a non-root user.
4. Set that user and keep `python app.py` as the container’s main command.
5. Build and run the assigned image with the usual lab label and local port mapping.
6. Confirm a nonzero process UID, no `/source` directory, and a health response reporting `dispatch-1`.

The checker tests the running identity, packaged files, and response.
It does not certify how the image was built; explain the two stages and compile step in your notes.
