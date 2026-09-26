## Compare your diagnosis

The wrapper started the real API as a background child and then returned successfully.
Docker follows the container's main process, so that clean exit ended the container rather than proving useful service operation.
A foreground server or an exec handoff gives the container the required lifetime.
Port changes or restart loops do not repair a wrapper that immediately exits again.

Which observation ruled out your first alternative explanation?
Which preservation constraint would a quick reset have violated?
What should an operator monitor to detect this failure earlier?
