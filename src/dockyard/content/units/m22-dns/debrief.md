# Debrief: Distinguish name resolution from Service programming

Resolving a newly created Service name proves a current DNS observation instead of relying on an old cached answer.
The returned ClusterIP and a request through it distinguish successful name resolution from successful Service programming.

## Explain your result

How would your diagnosis change if the name resolved correctly but the returned address could not carry a request?

## Transfer beyond this lab

Inspect resolver configuration, transport reachability, and backing Service state separately when diagnosing intermittent production DNS symptoms.
