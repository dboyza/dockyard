## Launching is not the same as serving

A container can start, run the command it was given, and finish successfully while doing nothing useful.
You found the command it really ran, explained why that made it stop, and checked the replacement both ways: its state and a real request.

You will see this pattern again in Kubernetes, where a Pod can report `Completed` when a service was expected to keep running.
Before moving on, write one sentence explaining why `Exited (0)` was not good news here.
