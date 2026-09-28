## Replace the process and keep the job

Build the supplied application and run the API with a writable bind mount from `$DOCKYARD_STORAGE` to `/data`.
Use your lab-terminal user and group numbers, the assigned container name, lab label, and local port.

Submit a job and record its identity.
Replace the container using the same mount, then find that job through `/jobs` again.
Leave the replacement running for the checker.

Before continuing, explain which data would disappear if you removed the container without a mount.
