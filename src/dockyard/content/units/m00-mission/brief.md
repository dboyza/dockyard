Read `HANDOVER.md` in your lab workspace, then make the welcome page work.

When you are done:

- `curl "http://127.0.0.1:$DOCKYARD_PORT/"` returns the welcome page from the `welcome` folder.
- The page is published only on `127.0.0.1`, on this lab’s assigned port.
- The container cannot change the files it serves.
- The container keeps this lab’s name and `io.dockyard.lab` label.

Before you replace anything, write down in your notes what was wrong with the original container and how you found out.
