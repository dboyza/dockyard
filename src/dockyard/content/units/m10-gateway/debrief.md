## Two links, both checked

The route needed to attach to the right Gateway and point at the right Service port.
The conditions told you each link was accepted, and the two requests showed traffic really flows only for the intended hostname.

Check your understanding:
Follow a request for `gateway.dispatch.test` from the listener, through the route, to a Dispatch Pod.
Which condition would have shown the wrong Service port, and which the missing Gateway?
