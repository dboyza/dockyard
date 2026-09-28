## Preparation, then work

The init container had to succeed before the worker could start, and the shared emptyDir carried its file to both the worker and the observer.
Because the file lives in the Pod, it disappears when the Pod is replaced, and the init container simply writes it again.

Check your understanding:
Why could a file written in a *different* Pod not satisfy this worker?
When would an init container be a better choice than making the application wait for its own dependencies?
