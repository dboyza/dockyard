## Reserve, cap, and budget

Requests decide where a Pod can go, limits cap what it can use, and namespace rules can refuse a Pod before it exists.
Each fails in its own recognisable way: Pending, OOMKilled or throttled, or an error at creation.

Check your understanding:
Which event or status would tell you a Pod is Pending for lack of CPU, and which would tell you a container was killed for memory?
What QoS class would a Pod with `requests` equal to `limits` for both CPU and memory have?
