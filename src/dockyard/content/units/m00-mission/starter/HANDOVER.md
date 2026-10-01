# Handover note

I started a container to serve the welcome page in the `welcome` folder.
`docker ps` says it is up, but the page never loads.
I ran out of time before I could work out why.

Requirements from the team:

- Serve `welcome/index.html` on this lab's assigned port.
- Only this computer may reach it.
- The server must not be able to change the files it serves.
- Keep the lab's container name and label so Dockyard can find it.
