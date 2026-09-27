# Debrief: Separate client access from control-plane health

The private guest client reaches the intended API endpoint using the cluster’s certificate-backed connection.
A failed client request can result from endpoint or trust configuration even when the control-plane processes themselves remain healthy.

## Explain your result

What host-side observation would separate an unavailable API process from a client that targets the wrong address?

## Transfer beyond this lab

Keep administrative client configuration scoped to the intended cluster and never repair a trust problem by disabling certificate verification.
