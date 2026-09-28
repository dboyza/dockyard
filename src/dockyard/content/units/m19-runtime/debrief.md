## From Kubernetes object to Linux process

`crictl` now reaches containerd through the right socket, and you followed a Dispatch container all the way to its Linux process and cgroup.
The containers were never affected; only the inspection tool was broken.

Check your understanding:
Why could Dispatch keep working while `crictl` was broken?
What is the difference between a container ID, a process ID, and a Pod name?
