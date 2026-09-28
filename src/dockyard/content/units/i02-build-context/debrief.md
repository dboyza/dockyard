## Compare your diagnosis

`release.sh` built from `staged-context`, an old folder left over from a previous packaging step.
The `VERSION` you edited was in the workspace folder, which that build never looked at.
The cache was doing its job correctly: the files it was given had not changed.
Pointing the build at the right folder fixes the cause; `--no-cache` would rebuild the same old files more slowly.

Check your understanding:
Which observation showed you the build was reading a different folder?
How could a team catch this before release, for example by checking the release reported by a freshly built image?
