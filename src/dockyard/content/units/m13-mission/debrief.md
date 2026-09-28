## A drain that kept serving

Placement let the API use both workers, autoscaling gave it room, and a realistic disruption budget let the drain proceed while protecting two copies.
With `minAvailable` equal to the replica count, the same drain would have waited forever, and that would have been the budget working as written.

Check your understanding:
What evidence told you it was safe to evict, and what would have made you stop and add capacity first?
