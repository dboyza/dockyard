## When kubectl exec is not enough

`kubectl exec` runs a command inside a container that is already running.
That covers many investigations, but two common situations defeat it.

- **The container has no tools.** Hardened images often leave out the shell, `ps`, and network utilities, so there is nothing to run.
- **The container keeps crashing.** It is only alive for a moment between restarts, so there is no running container to enter.

`kubectl debug` handles both.
It can add a temporary container to a running Pod, or start a copy of a Pod with changes that make it easier to explore.

```figure
ephemeral-debug
```

## Ephemeral containers

An **ephemeral container** is a container added to a Pod that is already running.
It brings its own image, so it can bring its own tools, and it never restarts.
The Pod is not recreated, so the application keeps running while you look.

```sh
kubectl debug API_POD --image="$DOCKYARD_BUSYBOX_LOCAL_IMAGE" --target=api --profile=general -- ps
```

Replace `API_POD` with the name of one API Pod from `kubectl get pods -l app=dispatch`.
`$DOCKYARD_BUSYBOX_LOCAL_IMAGE` is a small busybox image that this lab has already loaded into the cluster, so nothing is downloaded.

Each container in a Pod normally has its own **process namespace**: it sees only its own processes.
`--target=api` places the ephemeral container in the `api` container's process namespace instead, so `ps` lists the API's processes, starting with `python app.py` as process 1.
Without `--target`, `ps` would list only the debugging container's own commands.
`--profile=general` picks a sensible set of permissions for general debugging.

That command runs `ps` once and exits.
kubectl prints the new container's name, such as `debugger-x7k2p`, and its output is kept like any container's logs:

```sh
kubectl logs API_POD -c debugger-x7k2p
```

To explore interactively instead, add `-it` and run `sh`; type `exit` when you are done.
An ephemeral container stays listed in the Pod's spec after it exits, and cannot be removed; it disappears when the Pod is replaced.

## Debugging copies

A crashing container needs a different approach.
`--copy-to` creates a new Pod that copies an existing one, with changes you choose:

```sh
kubectl debug WORKER_POD -it --copy-to=worker-debug --container=worker -- sh
```

This creates a Pod called `worker-debug` whose `worker` container runs `sh` instead of its usual command, and attaches your terminal to it.
The image, files, environment variables, and mounted Secrets are the same as the original, so you see exactly what the crashing command saw.
The copy has no labels and belongs to no Deployment, so Services send it no traffic and the Deployment does not count it.

A copy keeps running, and holding its share of the node, until you delete it:

```sh
kubectl delete pod worker-debug
```

## The situation in this lab

A teammate changed the worker's command in `worker.yaml` to `python jobs.py`, believing the entry point had been renamed.
It had not.
The workers now exit straight after starting, and no jobs are processed.

Separately, the platform team wants evidence of what actually runs inside an API container, taken without restarting it.

## Fix it

1. Read `kubectl logs deployment/worker` and note which file Python could not open.
2. Start a debugging copy of one worker Pod with `sh`, list `/app`, and find the real entry point. Type `exit` when you have it.
3. Correct the command in `worker.yaml` and run `sh run.sh`.
4. Attach an ephemeral container to one API Pod with `--target=api` running `ps`, and save its output with `kubectl logs API_POD -c CONTAINER > api-processes.txt`.
5. Delete the debugging copy.

`kubectl get pods` should then show two running workers with no new restarts, no `worker-debug` Pod, and `api-processes.txt` should show `python app.py` as process 1.

## If something goes wrong

- **`ps` shows only `ps` itself**: the ephemeral container was started without `--target=api`. Start another one; each needs a new name, which kubectl picks for you.
- **`kubectl debug` reports that the Pod was not found**: it needs a Pod name, not `deployment/worker`. Copy one from `kubectl get pods -l app=worker`.
- **The copy exits at once**: without `-it`, `sh` has no input and finishes immediately. Delete the copy and start it again with `-it`.
