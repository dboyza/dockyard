# Read storage and scheduling together

Pending describes an incomplete transition, not a root cause.
With WaitForFirstConsumer, provisioning can wait until scheduling identifies an eligible node for the consumer.
That allows a local volume to be created where its Pod can run.
For example, a consumer requiring `disk: archive` cannot be placed if every node only advertises `disk: general`.
The storage controller can be healthy while the claim remains Pending because no consumer placement is possible.
Read claim events, the StorageClass, Pod events, and actual node labels before deleting a claim or changing storage provisioners.

A node selector expresses a required placement constraint.
Changing it is appropriate only when the chosen node satisfies the intended workload needs.
This lab uses an existing warm tier as the legitimate target; it does not require adding machines or simulating cloud topology.
