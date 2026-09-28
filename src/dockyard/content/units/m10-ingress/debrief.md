## Trust, name, and route

Your request passed three checks in turn: the certificate was trusted, it matched `dispatch.test`, and the Ingress rule sent the request to Dispatch.
Any one of them failing would have stopped it.

Check your understanding:
What would a successful request with `--insecure` fail to show?
What would you look at if the certificate check passed but you got a 404?
