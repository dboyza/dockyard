# Restore the TLS route

The Ingress selects a missing TLS Secret and sends traffic to a nonexistent Service port.
The prepared Secret `dispatch-tls` contains the practice certificate for `dispatch.test`.

Repair `ingress.yaml` to use that Secret and Service `dispatch` port 8080 with a Prefix route for `/`.
Keep ingress class `traefik` and the supplied secure entrypoint annotation.
Apply the change, inspect controller and resource status, and send the certificate-validated curl request from the example.
Do not use `--insecure` or replace the application response with a static page.
A passing check requires an actual Dispatch response over the validated TLS connection.
