## Confine the renderer and tidy the control plane

Requirements:

- **Control-plane footprint**: no service on the control plane exposes files to the network, and no leftover account there can use `sudo` or log in with a shell.
- **AppArmor**: the supplied `dockyard-renderer` profile is loaded and installed on both nodes, and the renderer runs under it in enforce mode.
- **seccomp**: the renderer runs with a seccomp filter.
- **Still working**: the renderer keeps adding pages to `/output`, and Dispatch keeps processing jobs.

The renderer must keep running as root, and the original namespace, nodes, marker object, and stored data must remain.

Write `confine-report.md` describing what you found, what you changed, the evidence, and the risks that remain.
Then compare it with `report-rubric.md`.
