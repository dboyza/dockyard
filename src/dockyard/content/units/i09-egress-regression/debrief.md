## Compare your diagnosis

There were two faults.
DNS egress no longer allowed UDP, so name lookups failed, and the workers’ rule for Redis named the wrong port.
Fixing DNS alone made the API look healthy while jobs still never finished; only fixing the queue rule too restored background processing.
Any narrow set of rules that restores these paths while keeping the blocked ones blocked is a valid fix.

Check your understanding:
How would an allow-everything policy have made the frontend test pass while breaking the requirements?
