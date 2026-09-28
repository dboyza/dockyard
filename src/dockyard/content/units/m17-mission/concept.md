## Secure, and still working

This mission combines the whole security module.
Four separate controls protect Dispatch, and each one is currently weaker than it should be:

- **API permissions**: an identity can read Secrets it does not need.
- **Network rules**: a frontend peer is too broad, and DNS is only partly allowed.
- **Admission**: the namespace does not enforce the Restricted standard.
- **Process restrictions**: the API runs with more privilege than it needs.

Tightening them is only half the job.
A system that blocks everything is not secure, just broken.
For each control, show one thing that should work *does* work, and one thing that should be blocked *is* blocked for the right reason.

The lab gives you what you need to test that: two nodes, three distinguishable clients, and an outside target the API must not reach.
Keep the database password in its Secret and out of your files and notes.

There are no step-by-step commands; everything you need is in this module’s lessons.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
