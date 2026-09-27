# Debrief: Separate gateways from application routes

Gateway infrastructure and application routes have separate configuration and status boundaries.
Accepted and resolved route conditions are useful observations, but the matching-host response and unmatched-host rejection establish actual routing behavior.

## Explain your result

Trace how a hostname reaches the listener, HTTPRoute, Service port, and application, then identify where an unresolved reference would interrupt that path.

## Transfer beyond this lab

When ownership is split across teams, use Gateway API attachment and reference rules to make those boundaries explicit.
