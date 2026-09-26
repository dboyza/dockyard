# Attach and verify the application route

The supplied HTTPRoute names a Gateway that does not exist and a backend Service port that is not exposed.
Repair `gateway.yaml` while preserving hostname `gateway.dispatch.test`, Gateway `dispatch-gateway`, and the supplied listener.
Apply the file, inspect current Gateway and route conditions, and test a real request with the matching Host header.
Then test `unmatched.dispatch.test` and verify it returns 404 instead of reaching Dispatch.

Do not add a wildcard hostname or a catch-all route to make one request pass.
Explain why the HTTPRoute's parent attachment and its backend reference are separate relationships.
