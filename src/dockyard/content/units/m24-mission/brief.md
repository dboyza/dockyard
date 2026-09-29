## Keep Dispatch running through a control-plane outage

- Leave the first control-plane node's API server and etcd member stopped, and keep all three etcd memberships.
- Make the cluster's API address work again, and show the API accepts new changes.
- Get Dispatch finishing jobs again, with the API inside the agreed CPU, memory, and disruption budget.
- Limit `dispatch-reader` to reading Pods in `dispatch`.
- Build and roll out the release with `VERSION` set to `dispatch-handoff-v1`, for both the API and the workers.
- Keep the original cluster and database data, and write `handoff.md`.
