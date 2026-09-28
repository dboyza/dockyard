## Reconnect the Service to its Pods

Make the existing `dispatch` Service reach exactly the two ready Dispatch API Pods again.

- Keep the Service’s name and port, the database’s storage, and the original job.
- Do not write EndpointSlices by hand, and do not point clients at a Pod IP instead of the Service.
- Submit a new job through the Service and confirm a worker completes it.

In your notes, record the first observation that pointed at the cause, your fix, and a check you could run to catch this after future releases.
