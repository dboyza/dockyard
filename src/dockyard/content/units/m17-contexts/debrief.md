# Debrief: Enforce and observe runtime restrictions

Admission decides whether a proposed Pod configuration is accepted, while process observations show the restrictions that actually reached a running container.
Non-root identity, dropped capabilities, seccomp filtering, and a read-only root filesystem address different forms of runtime authority.

## Explain your result

Why would an admission label alone be insufficient evidence that an already running workload has the intended restrictions?

## Transfer beyond this lab

Provide explicit writable locations for legitimate application state instead of weakening the entire runtime boundary.
