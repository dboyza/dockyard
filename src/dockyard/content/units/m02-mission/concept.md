## Give another person a release they can run

You have practised building an image, updating a running release, and separating build work from runtime files.
Now combine those skills without a complete command sequence.
The application code is supplied; your work is the Dockerfile, the running container, and a clear explanation of how to reproduce the result.

Start from this lab’s files even if you still have containers from earlier lessons.
Each lab has its own names and workspace.
The image stays on your computer; the registry lessons later show how to distribute it.

Before building, identify which stage will check the source, which files the final stage needs, and which user will run the API.
After building, test the running container rather than assuming the Dockerfile guarantees the result.
The check verifies the response, non-root user, and absence of host mounts and `/source`.
Your explanation of the build process is self-review.
