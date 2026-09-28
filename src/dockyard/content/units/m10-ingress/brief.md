## Fix the HTTPS route to Dispatch

The Ingress points at a TLS Secret that does not exist and at a Service port nothing listens on.
The Secret `dispatch-tls` already holds the practice certificate for `dispatch.test`.

1. Inspect the Ingress, its class, and the Secret.
2. Fix `ingress.yaml` so it uses `dispatch-tls` and sends `/` (Prefix) to Service `dispatch` on port 8080. Keep class `traefik` and the supplied annotations.
3. Apply it and run the certificate-checked curl command from Understand.
4. Choose **Check work**.

Do not use `--insecure`, and do not replace Dispatch with a static page: Check work needs a real Dispatch response over a verified connection.
