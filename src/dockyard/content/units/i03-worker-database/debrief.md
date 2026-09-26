## Compare your diagnosis

The API and worker ran the same artifact with different effective database settings.
A healthy API only verified its own dependency configuration.
Correcting the worker overlay restored the background transaction without replacing storage or exposing PostgreSQL to the host.
The observed worker identity and persisted result provide stronger evidence than container counts alone.

Which observation ruled out your first alternative explanation?
Which preservation constraint would a quick reset have violated?
What should an operator monitor to detect this failure earlier?
