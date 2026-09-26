Restore the private API endpoint while leaving the primary API server and etcd member stopped.
Preserve all three original etcd voting members.
Both surviving etcd endpoints must be healthy, the private endpoint must accept a fresh write/read/delete, and Dispatch must complete a fresh job.

Inspect and repair the worker's HAProxy configuration, validate it, and reload HAProxy.
A correct configuration can select either or both healthy API servers; no exact backend ordering is graded.
Do not restore the primary components as a substitute for demonstrating failover.
Record the remaining endpoint, storage, and host failure points in your notes.
