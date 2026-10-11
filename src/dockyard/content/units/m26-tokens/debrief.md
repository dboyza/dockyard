## What changed

The viewer no longer carries a token it never used, the never-expiring legacy token is gone, and the default ServiceAccount has no permissions.
The builder runs as its own identity, which can read exactly one ConfigMap and nothing else, and it keeps working.

Check your understanding: if an attacker had copied the legacy token last month, what could they still do now, and what if you had only removed the RoleBinding?
Why did the viewer need a restart, while the builder picked up its new identity from your apply?
