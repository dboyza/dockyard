## What you’re walking into

This is an **incident**: something is broken, and you have to find out why before you fix it.
There is no worked example; use what you learned about containers, logs, and Dockerfiles.

The report from the team:

- A new start-up script, `launch.sh`, was added to the Dispatch image just before the problem began.
- Every launch prints “Launch wrapper completed successfully”.
- The container then shows `Exited (0)`, and nobody can reach Dispatch.

## How to approach an incident

1. **Describe the symptom** in one sentence, in terms a user would notice.
2. **Collect evidence** before changing anything: the container’s state, its command, and its logs.
3. **Form a theory** that explains all of that evidence, not just part of it.
4. **Make the smallest fix** that addresses the cause.
5. **Check the result** the way a user would, with a fresh request.

Write each step in your notes as you go.
Hints and the reference solution are available, but using them marks this attempt as practice with help.

## Useful reminders

A **wrapper script** is a small shell script that starts the real program, often after some preparation.
In a shell script, `&` at the end of a line starts that program in the background and moves straight on to the next line.
The container lives only as long as its main process, which here is the shell running `launch.sh`.

The script is baked into the image.
After editing it, rebuild the image with the `BASE_IMAGE` argument, as in the Dockerfile lesson, and replace the stopped container.
