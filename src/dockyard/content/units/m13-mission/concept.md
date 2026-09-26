# Mission: capacity must survive a planned transition

The application pool exists, but incorrect placement rules keep API Pods from using it, the HPA targets the wrong Deployment, and the disruption budget permits no loss of availability at the intended four-replica size.
Repair the operating envelope before attempting maintenance.
The source of evidence is the real scheduler, metrics API, HPA controller, eviction API, and application Service.

The supplied drain rehearsal chooses only a worker in this private cluster's application pool.
It records current API Pod UIDs, samples readiness through the assigned loopback NodePort while draining, uncordons the worker, and waits for the workload to converge again.
It writes the observation to `drain-evidence.json` for inspection.
That record is a sampled local rehearsal, not proof of a production SLO or every request made between samples.

## Eviction and request draining are separate

EndpointSlice updates and process termination proceed asynchronously when a Pod is deleted.
The supplied API has a five-second preStop sleep within its twenty-second termination grace period, allowing endpoint routing changes to propagate before SIGTERM closes the server.
This is a measured local drain allowance, not a guarantee for arbitrary load balancers or long-lived connections.
A PDB constrains the number of voluntary evictions; it does not drain individual network requests.
After replacement, the rehearsal also waits for Metrics Server to observe the new Pod identities before assessing scaling.
See the [official termination flow](https://kubernetes.io/docs/tutorials/services/pods-and-endpoint-termination-flow/) for the relationship between terminating endpoints and serving traffic.
