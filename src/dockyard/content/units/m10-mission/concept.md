## Four ways in, four separate faults

Dispatch is running fine, but every way of reaching it is broken in a different place.
This mission brings together everything in this module: Services, LoadBalancers, Ingress with HTTPS, and Gateway API.

Fixing one path proves nothing about the others, even though they all lead to the same Pods.
Work through them one at a time, and test each with a real request:

1. **Inside the cluster**: the `dispatch` Service, tested with `kubectl exec`.
2. **LoadBalancer**: `dispatch-public`, tested from a container on the Docker network.
3. **HTTPS Ingress**: `dispatch.test`, tested with curl while checking the certificate.
4. **Gateway API**: `gateway.dispatch.test`, plus an unmatched hostname that must return 404.

For each one, note which client sent the request and which network it could reach.
There are no step-by-step commands; the test commands from the three lessons all still apply.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
If you used help, try again later from a fresh lab to show yourself you can do it unaided.
