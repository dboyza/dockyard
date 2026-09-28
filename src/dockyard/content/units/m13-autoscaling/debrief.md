## Scaling from real measurements

The HPA measured CPU against each Pod’s request and added copies up to its limit.
The disruption budget now makes sure planned maintenance never leaves fewer than two copies serving.

Check your understanding:
Pods request 100m CPU, the target is 60%, and average use is 90m. Roughly how many replicas would the HPA aim for, compared with now?
Why would more API copies not help if the real bottleneck were the database?
