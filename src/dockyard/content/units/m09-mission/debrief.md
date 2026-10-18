## Same image, different behavior

Each environment got its settings and password from its own namespace, and both processed real jobs.
That shows configuration and identity are separated.
It does not show the environments are isolated from each other’s network traffic.

Check your understanding:
What would you look at to prove preview is not accidentally reading the `dispatch` ConfigMap?
What would you add before trusting this setup with environments that must not be able to reach each other?
