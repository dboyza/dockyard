## The container is up, but the page never loads

A teammate started a container to serve a welcome page, then left you a note in `HANDOVER.md`.
`docker ps` says the container is up, yet nobody can load the page.
Your job is to find out why and leave a container that meets the team’s requirements.

This is a **mission**: it describes the result you need, not the commands to type.
Everything you need was covered in this module.

## Investigate before you change anything

Resist the urge to start a new container straight away.
Look at the one that exists and answer these questions first:

- Is the container running, and what does its PORTS column show?
- Which port does Docker forward requests to inside the container?
- Which port is the server inside actually listening on?
- Which folder is mounted, where does it appear, and can the container write to it?

`docker ps --no-trunc` shows the full command a container runs.
`docker port` shows its published ports.
`docker inspect` shows everything else as a long JSON document; scroll to its `Mounts` section, where `"RW": true` means the container can write to that folder.

Remember that **Up** only tells you the main process is running.
It says nothing about whether requests can reach that process.

## Working on your own

Try the mission without hints first.
Hints and the reference solution are there if you get stuck, but using them marks this attempt as practice with help.
Any commands that produce the required result are accepted.
