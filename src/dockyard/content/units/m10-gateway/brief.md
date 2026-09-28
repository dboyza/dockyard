## Attach the route and test it

The HTTPRoute names a Gateway that does not exist, and sends traffic to a Service port that is not open.

1. Inspect the Gateway and the HTTPRoute’s status conditions.
2. Fix `gateway.yaml` so the route attaches to `dispatch-gateway` and sends traffic to Service `dispatch` on port 8080. Keep the hostname `gateway.dispatch.test` and the existing listener.
3. Apply it and check the route’s conditions are now `True` and current.
4. Test `gateway.dispatch.test`, which should reach Dispatch, and `unmatched.dispatch.test`, which should return 404.
5. Choose **Check work**.

Do not add a wildcard hostname or a catch-all route.
In your notes, explain why the route’s parent and its backend are separate links.
