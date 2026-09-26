# Trace the entire request

Describe the destination used by the client, the controller or proxy that handled it, the selected Service port, the backend endpoint, and the application listener.
For TLS, distinguish certificate trust, hostname verification, and HTTP routing after the handshake.
For Gateway API, compare declared intent with Accepted, ResolvedRefs, and Programmed conditions before looking at a real response.

Explain why a successful request through one exposure method does not establish that the others work.
Document the macOS boundary: the Docker network is inside Docker's Linux environment, while loopback NodePort mappings are directly reachable from this Mac.
The private-network client is external to Kubernetes, but it is not a public internet client.
