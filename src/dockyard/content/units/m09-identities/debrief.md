## An identity, a Role, and the binding between them

The Role was right and the ServiceAccount was right; the binding connected the Role to the wrong subject.
The Pod’s own request returned 200 for what it needs and 403 for everything else, which is exactly the result you want.

Check your understanding:
Trace the chain for the allowed request: which subject, which binding, which Role, which verb, which resource, which namespace?
Why does a successful `kubectl get pods` from your terminal tell you nothing about the inventory Pod?
