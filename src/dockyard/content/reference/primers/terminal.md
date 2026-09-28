# Terminal basics

A **terminal** is a window where you type commands instead of clicking.
The program that reads what you type and runs it is called the **shell**.
Docker and kubectl are ordinary programs that you start from the shell.

When Dockyard opens a lab terminal, it starts you in the lab’s own folder with some helpful values already set.

## Where am I?

```sh
pwd
ls -la
```

`pwd` prints the folder you are in, called the **working directory**.
`ls` lists the files there; `-la` adds hidden files, whose names start with a dot, and details such as sizes and permissions.

A **path** is a file’s location.
`Dockerfile` on its own means “the file called Dockerfile in the current folder”; this is a **relative path**.
A path starting with `/`, such as `/tmp/example`, is an **absolute path**: it means the same place wherever you are.
`cd folder` moves into a folder, and `cd ..` moves up one level.

## Reading and writing files

`cat file` prints a file’s contents.

To change a file, open it in any text editor, save it, then check it with `cat`.
If you prefer to stay in the terminal, `nano file` opens a simple editor: Control-O then Enter saves, and Control-X exits.

You can also write a short file directly from the shell:

```sh
cat > practice.txt <<'EOF'
This is the first line.
This is the second line.
EOF
cat practice.txt
```

Everything between the two `EOF` lines is written into `practice.txt`.
The closing `EOF` must be on its own line with nothing before it.
Be careful: `>` replaces a file that already exists, so check the name first.

## Variables

The shell can store named values called **variables**.
Values the shell passes on to every program it starts are called **environment variables**.
Writing `$NAME` inserts a variable’s value into a command:

```sh
echo "$DOCKYARD_WORKSPACE"
```

Dockyard sets variables such as `$DOCKYARD_CONTAINER` and `$DOCKYARD_PORT` in every lab terminal.
Type them exactly as shown in the lessons; the shell fills in the real values for you.

Put variables inside double quotes, as in `"$DOCKYARD_PORT"`.
Double quotes keep the value together as one piece even if it contains spaces.
Single quotes, as in `'$HOME'`, stop the shell replacing anything, so the text is used exactly as typed.

## The parts of a command

In `kubectl get pods -n dispatch`:

- `kubectl` is the program.
- `get` and `pods` are **arguments**: words passed to the program.
- `-n dispatch` is an **option**, a setting that starts with a dash. Here it means “in the dispatch namespace”, which is a Kubernetes idea, not a folder on your computer.

When a lesson shows a placeholder such as `<the digest you found>`, replace the whole thing, including the angle brackets.
The shell treats `<` and `>` specially, so never type them literally.

A long command can be split over several lines by ending each line with a backslash, `\`.
You can paste such a block all at once.

## Output, errors, and chaining commands

Programs print normal output and error messages on two separate channels, called **standard output** and **standard error**.

- `command > file` saves the output to a file, replacing it.
- `command >> file` adds the output to the end of a file.
- `command 2>&1` sends error messages to the same place as normal output.
- `first | second` passes the output of the first command into the second. This is called a **pipe**.

```sh
printf 'worker\napi\n' | sort
```

Every command finishes with an **exit status**, a number the shell keeps.
Zero means success; anything else means the program reported a problem.
`echo $?` shows the status of the command you just ran.
`first && second` runs the second command only if the first succeeded.

A command reporting success does not always mean the result is what you wanted.
Check the file, container, or response you care about.

## Stopping a command

Control-C stops the command running in the foreground.
It does not undo anything the command already created, so check the lab’s state before trying again.

## Which computer am I on?

Some later labs use Linux virtual machines.
A command such as `limactl shell --workdir=/tmp "$DOCKYARD_WORKER"` takes you inside one of them, and everything you type runs there until you type `exit`.
`sudo` runs a single command with administrator rights.
Inside a lab machine that affects only the lab machine; on your own computer it affects your computer, so use it only where a lesson asks.

The lab terminal runs with your normal user permissions.
Its variables point commands at the lab’s resources, but it is not a security sandbox.

## Check your understanding

`kubectl get pods -n dispatch` and `ls dispatch` both mention “dispatch”. What is each one looking at?
Before running a command that changes something, can you say which program it runs, what it changes, and what you expect to see afterwards?
