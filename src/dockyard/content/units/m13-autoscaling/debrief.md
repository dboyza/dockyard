# Capacity is an observed operating envelope

Explain the difference between scheduling requests, runtime limits, measured usage, and namespace admission budgets.
Trace why each API Pod can or cannot land on each node, including labels, affinity, taints, tolerations, and topology spread.
For autoscaling, compare the measured CPU utilization with its request denominator and the desired replica count.

Describe what the disruption budget protected during voluntary eviction and what it cannot guarantee during involuntary failure.
The drain rehearsal records sampled readiness through the real Service; it does not establish a production SLO or zero lost requests between samples.
The small local cluster shares one Mac and Docker VM, so its nodes are not independent physical failure domains.
