## Two out of three is enough

With one control-plane node down, the other two still had an etcd majority, and once HAProxy knew about them, the API worked again.

Check your understanding:
Why could etcd be healthy while every kubectl command failed?
Why would removing the failed etcd member have changed what you were asked to prove?
How many members would you need to survive two failures?
