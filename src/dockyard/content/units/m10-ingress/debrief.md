# Debrief: Terminate TLS at an ingress controller

The ingress controller terminates a certificate-validated TLS connection before forwarding HTTP to the selected Service.
Hostname verification, certificate trust, and application routing must all succeed for the observed response to establish the intended route.

## Explain your result

What would a successful request with certificate verification disabled fail to demonstrate?

## Transfer beyond this lab

Production ingress also requires certificate lifecycle management and an exposure design beyond this Mac-local endpoint.
