## Fix the network rules

Two things are wrong in `network.yaml`:

- `allow-business-reads` has its namespace selector and Pod selector in separate list items, so either one alone lets traffic in.
- The DNS rule allows only UDP.

1. Fix both, keeping the default-deny policy and the other required rules.
2. Apply it with `python render.py network.yaml | kubectl apply -f -`.
3. Choose **Check work** and read which connections were allowed and denied.

The trusted frontend must reach the API across nodes; an untrusted frontend and the trusted label in the wrong namespace must not.
DNS must work over UDP and TCP, the frontend must not reach the database, and the API must not reach the outside test target.
