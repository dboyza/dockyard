## Compare your diagnosis

The build cache correctly reused layers for unchanged files in the stale staged context.
The edited root VERSION was never part of that build input.
Selecting the correct context repairs the input boundary; deleting the entire Docker cache would waste work without correcting the release script.
The final health response comes from a self-contained image, not a source bind mount.

Which observation ruled out your first alternative explanation?
Which preservation constraint would a quick reset have violated?
What should an operator monitor to detect this failure earlier?
