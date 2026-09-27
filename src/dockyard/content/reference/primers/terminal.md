# Read a terminal command before running it

A terminal is a window connected to a shell.
The shell parses your text, expands variables and patterns, and starts programs with arguments.
Docker and kubectl are programs you run through that shell; they do not replace it.
Dockyard opens a real shell in the current lab workspace with explicit lab identity and tool paths.

## Establish where you are

```sh
pwd
ls -la
printf '%s\n' "$DOCKYARD_UNIT" "$DOCKYARD_WORKSPACE"
```

`pwd` prints the working directory.
A relative path such as `Dockerfile` is resolved from that directory; `/tmp/example` is an absolute path.
`$DOCKYARD_UNIT` expands to an environment variable's value.
Double quotes preserve that expanded value as one argument even when it contains spaces.
Single quotes preserve literal text, including dollar signs.

## Separate the command from its arguments

In `kubectl get pods -n dispatch`, the program is `kubectl`; the remaining words are arguments.
`-n dispatch` selects a Kubernetes namespace, not a directory on your host computer.
In `docker logs CONTAINER`, replace `CONTAINER` with an actual identifier you observed.
Do not type angle-bracket placeholders literally: the shell gives `<` and `>` special meanings.

## Understand input, output, and failure

A program receives standard input and produces standard output and standard error.
`>` replaces a file with standard output; `>>` appends; `2>` redirects standard error.
A pipe passes one program's standard output into another program's standard input.

```sh
printf 'api\nworker\n' | sort
```

This sorts two supplied lines without modifying a lab resource.
An exit status of zero conventionally means success; a nonzero status means the program reported failure.
`command-a && command-b` runs the second command only after the first succeeds.
A pipeline's default status may reflect only its last command, so a quiet pipe is not sufficient verification that every stage worked.
Check the resulting files or live resources as well.

## Know which machine receives the command

`limactl shell --workdir=/tmp "$DOCKYARD_WORKER"` enters the owned Linux guest.
Commands entered there run inside that VM until you type `exit`.
`sudo` inside the guest grants guest-root privileges; `sudo` in your host computer shell is a different boundary.
The lab shell retains your ordinary host permissions, so its identifying variables are helpful scoping, not an operating-system sandbox.
Use the lab's supplied private kubeconfig and guest names.

## Recover your bearings

Control-C asks the foreground program to interrupt its current operation.
It does not undo resources the program already created.
After interruption, inspect actual lab state before retrying or cleaning up.
If you opened a terminal for another lesson, return to the browser and open a new terminal for the intended lab rather than silently retargeting the old one.

## Check your understanding

Explain why `kubectl get pods -n dispatch` and `ls dispatch` inspect different things.
Before running a mutation, identify its program, target environment, arguments, and expected observable result.
