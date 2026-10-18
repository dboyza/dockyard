# HTTP requests

**HTTP** is the language browsers and programs use to talk to web services.
Dispatch is a web service, so almost every lab involves sending it HTTP requests with `curl`.

## Requests and responses

A **request** says what you want:

- a **method**, such as `GET` to read something or `POST` to send something new;
- a **path**, such as `/jobs`;
- optional **headers**, extra details such as the format of the data;
- an optional **body**, the data itself.

The server replies with a **response**: a **status code** saying how it went, headers, and a body.

```figure
http-exchange
```

## Reading a URL

In `http://127.0.0.1:8080/jobs`:

- `http` is the protocol;
- `127.0.0.1` is the address of the machine to contact;
- `8080` is the **port**, which service on that machine to talk to;
- `/jobs` is the path within that service.

```figure
url-anatomy
```

`127.0.0.1`, also called **localhost**, always means “the machine making this request”.
Inside a container, that is the container itself, not your computer or a neighboring container.
Containers in the same Kubernetes Pod share one network, so for them localhost does reach each other.

```figure
localhost-perspective
```

## curl

```sh
curl http://127.0.0.1:8080/healthz
curl --include http://127.0.0.1:8080/healthz
curl -H 'Content-Type: application/json' -d '{"title":"hello"}' http://127.0.0.1:8080/jobs
```

The first line sends a GET and prints the body.
`--include` also prints the status and headers.
The third sends a POST: `-d` supplies the body, and `-H` adds a header saying the body is JSON.

By default curl reports success whenever any response arrives, even an error page.
Add `--fail` to make it treat error statuses as failures, or `--fail-with-body` to also see the error message.
`--max-time 5` stops waiting after five seconds.

## Status codes

| Status | Meaning |
| --- | --- |
| 200 | Success. |
| 201 | Success, and something new was created, such as a job. |
| 400 | The server thinks the request itself is wrong. |
| 401 | You need to log in, or your login was not accepted. |
| 403 | You are identified, but not allowed to do this. |
| 404 | There is nothing at that path. |
| 500 | The server hit an error while handling the request. |
| 503 | The server cannot handle requests right now, often because something it depends on is unavailable. |

Codes starting with 2 mean success, 4 means a problem with the request, and 5 means a problem on the server.

## When a request fails

The error message tells you how far the request got:

- **Could not resolve host**: the name could not be turned into an address. See the DNS primer.
- **Connection refused**: the address was reached, but nothing is listening on that port.
- **Empty reply from server**: something accepted the connection but closed it without answering. With Docker, this often means a published port leads to a container port where nothing is listening.
- **Timed out**: no answer came back in time. Something along the way is dropping or blocking traffic, or the service is stuck.
- **Certificate or TLS error**: a secure connection could not be verified.
- **An HTTP status**: the service answered. Read the status and body to see what it said.

Work out which of these you have before changing anything.

```figure
request-stages
```

## Dispatch’s check addresses

- `/healthz` answers if the Dispatch process is up and responding.
- `/readyz` also checks that Dispatch can reach its database and queue.
- `/startupz` answers once Dispatch has finished starting.

Submitting a job and watching it finish tests far more than any of these on its own.
`/healthz` can succeed while `/jobs` fails, for example when the database is down.

## Check your understanding

How can `/healthz` succeed while submitting a job fails?
If a request fails, what is the first thing you would look at to decide whether the problem is the name, the port, or the application?
