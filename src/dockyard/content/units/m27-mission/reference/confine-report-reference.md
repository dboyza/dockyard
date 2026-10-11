# Confinement report

## Findings and fixes

- The control plane ran `debug-share`, serving `/var/log` to the network on port 2222. Disabled and masked it; the port is closed.
- The `contractor` account had passwordless `sudo` on the control plane. Removed its sudo rule and set its shell to `/usr/sbin/nologin`.
- The renderer ran as root with no AppArmor profile and no seccomp filter. Loaded `dockyard-renderer` on both nodes and applied it, with the runtime's default seccomp profile.

## Evidence

- `ss -ltnp` on the control plane shows nothing on port 2222.
- The renderer reports `dockyard-renderer (enforce)` and `Seccomp: 2`, a write to `/etc` fails, and it keeps adding pages to `/output`.

## Remaining risks

- The renderer still runs as root because its vendor image requires it; ask the vendor for a non-root image.
- The seccomp profile is the runtime default; an allowlist profile would be stronger.
