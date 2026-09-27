# Debrief: Separate requests, limits, and admission budgets

Requests inform scheduling, limits constrain runtime use, and admission policies can reject configurations before a Pod is created.
Looking at these boundaries separately explains why an unschedulable request and a runtime memory termination need different repairs.

## Explain your result

Which observation would distinguish insufficient schedulable capacity from an application exceeding its memory limit?

## Transfer beyond this lab

Choose production requests and limits from measured workload behavior, leaving headroom for node services and transient demand.
