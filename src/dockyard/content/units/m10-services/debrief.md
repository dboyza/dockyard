# Debrief: Trace Services from DNS to real traffic

Service DNS, endpoint selection, NodePort exposure, and LoadBalancer addressing each add a different part of the request path.
The EndpointSlice evidence connects the selected backends to the owned ready API Pods rather than to an unrelated responder.

## Explain your result

Explain why a successful loopback NodePort request does not demonstrate that the private LoadBalancer address works.

## Transfer beyond this lab

The external client in this lab is outside Kubernetes on a private network, not a public internet client or a cloud load balancer.
