# Trace an HTTP request through its boundaries

An HTTP request names a method, a target path, headers, and sometimes a body.
A response has a status, headers, and a body.
The same application can be healthy at one path and broken at another because the paths exercise different dependencies.

## Read the URL

In `http://127.0.0.1:8080/jobs`, `http` is the scheme, `127.0.0.1` is the host, `8080` is the port, and `/jobs` is the path.
The loopback address identifies the machine or network namespace making the request.
Inside a container, `127.0.0.1` refers to that container's network namespace, not automatically to your Mac or another container.
A Pod's containers share a network namespace, which is why sidecars can communicate over localhost.

## Observe a public example without changing data

```sh
curl --include --max-time 5 https://example.com/
```

`--include` shows response headers, and `--max-time` bounds how long the request can take.
This example needs an internet connection; Dockyard's prepared lab requests use local endpoints.
A GET conventionally reads a representation.
A POST submits a body for the server to process, such as creating a Dispatch job.
A DELETE requests removal of the named resource.
The application's actual API defines the behavior; the method name alone does not prove that a request is harmless or idempotent.

## Classify the failure before choosing a repair

A DNS error means the name was not resolved as needed.
A connection refusal means no accepting TCP path was available at the chosen address and port.
A timeout means the operation did not finish before its deadline; it does not uniquely identify the failed layer.
A TLS validation error means the expected secure identity or trust could not be established.
An HTTP response proves that an HTTP-speaking peer answered, but the status and body determine what it reported.

| Status | Useful interpretation |
| --- | --- |
| 200 | The request succeeded according to this endpoint. |
| 400 | The server rejected the request as invalid. |
| 401 | Authentication was required or failed. |
| 403 | The request was forbidden by the server's policy. |
| 404 | The requested resource or route was not found. |
| 500 | The server encountered an internal failure. |
| 503 | The service could not handle the request at that time. |

`curl` can exit successfully after receiving an HTTP error response unless you ask it to treat that status as a failure.
Use `--fail-with-body` when you want a failing exit status while retaining the diagnostic response body.
Do not equate a shell exit code with an application result without checking those semantics.

## Understand Dispatch's probes

`/healthz` answers whether the application process can respond.
`/readyz` additionally checks dependencies needed to serve work.
`/startupz` represents completion of startup.
Submitting a new job and verifying its completed database result exercises more of the system than any one probe.
These checks complement one another; they are not interchangeable definitions of success.

## Check your understanding

Explain how `/healthz` can succeed while `/jobs` fails.
For a failed request, record the first boundary that did not work and one observation that would challenge your hypothesis.
