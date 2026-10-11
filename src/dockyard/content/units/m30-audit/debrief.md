## What changed

The API server now records who accesses Secrets, without their contents, and full detail for workload changes, with rotation so the log cannot fill the disk.
That record named the reader: the `metrics-exporter` ServiceAccount in `telemetry`, which had been granted access to the database password.

Check your understanding: the exporter's access was granted by a RoleBinding.
What would you do next, and which audit entries would tell you who created that binding?
Why would `RequestResponse` for every request have been worse than useless?
