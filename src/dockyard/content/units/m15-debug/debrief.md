## What changed

The workers run again because their command names the file that exists, `worker.py`.
The debugging copy let you see the container's files with the same image, environment, and mounts as the crashing Pod, without changing the Deployment.
The ephemeral container joined a running API Pod and, with `--target=api`, shared its process namespace, which is why `python app.py` appeared as process 1.

Check your understanding: why does the ephemeral container stay listed in the API Pod's spec, and what would remove it?
When would you choose `--copy-to` over an ephemeral container?
