## Get Dispatch running again

When you prepare the lab, you get a container whose program has already finished with exit code 0.
The supplied `app.py` is correct and does not need editing.

Get a Dispatch API running that keeps running, using this lab’s container name, label, and host port.
Publish it only on `127.0.0.1`, and make sure `/healthz` answers with service `dispatch`.
Leave other containers and the supplied image alone, and leave your repaired container running.

In your notes, answer three questions:

1. What command did the broken container run?
2. Why did it finish instead of serving requests?
3. Which two observations show that your replacement works?

Check work tests the repaired service; your answers are for your own review.
Everything you need was introduced earlier in this module.
