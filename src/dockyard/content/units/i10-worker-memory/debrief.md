## Compare your diagnosis

The new memory limit was smaller than the worker needs.
The kernel killed each worker as soon as it used more memory than the limit allowed.
The workers never lived long enough to finish jobs.
`OOMKilled` in the last state pointed straight at memory rather than at probes or code.
A limit with room for the working set and Python’s own needs let the workers run steadily.

Check your understanding:
Why did raising only the memory request not help?
A few minutes of stability is encouraging, but what would you measure over days before trusting a production memory limit?
