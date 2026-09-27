You ran a real application inside a Linux container and verified it from the host computer.
The image supplied the runtime filesystem, the container supplied an instance of that environment, and the main process determined whether it kept running.
The port mapping connected a host endpoint to the process's listening port.

Before moving on, explain what would happen if you removed the container but kept the image.
Then consider why a detached container can still exit immediately.
If either answer is uncertain, repeat the stop/start observation and inspect `docker ps -a`.

The next lesson distinguishes stopping, removing, and recreating a container, including what happens to its writable layer.
