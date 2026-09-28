## The whole delivery chain

A release passes through several systems, and each proves one thing:

- The pipeline shows the image passed its tests.
- The registry shows the image can be pulled.
- A Git commit shows which image each environment should run.
- Flux shows that commit was applied.
- The running application shows it actually works.

A break anywhere stops the release, and a success at one step says nothing about the next.

In this mission, the test gate has been bypassed and both environments are suspended.
Repair them, publish a tested release, and demonstrate the full cycle from the promotion lesson.
The supplied helper scripts are there to use, but work out what is wrong at each step yourself before running them.

Be honest about this setup’s shortcuts in your notes: an unauthenticated local registry, shared practice dependencies, unsigned evidence files, and a small single-node cluster.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
