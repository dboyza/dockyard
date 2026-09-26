## Harden the supplied API

Prepare starts a working non-root API without the required runtime restrictions.
Replace it with a read-only root filesystem, all capabilities dropped, and no-new-privileges enabled.
Set memory between 32 and 256 MiB, a positive CPU quota no greater than one CPU, and a process limit between 16 and 256.
A useful reference setting is 128 MiB, half a CPU, and 64 processes.

Keep the process non-root and the existing loopback/ownership contract.
The API must still answer `/healthz` successfully.
Inspect the active cgroup limits and explain why the supplied stateless API can use a read-only root filesystem without an additional writable data mount.
