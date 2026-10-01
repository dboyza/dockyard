Let’s find out where a container keeps the changes it makes.
Use the commands in Understand as you work through these steps.

1. Prepare the lab and open its terminal.
2. Look at the image’s layers with `docker history`.
3. Start a container that stays running, using `-d` and `sleep infinity`.
4. Use `docker exec` to list its processes, then to write and read `/tmp/note.txt`.
5. Find the note with `docker diff`, and confirm that a fresh throwaway container does not have it.
6. Leave your container running and choose **Check work**.

You’re ready to check when `docker ps` shows your container running and `docker diff` lists `A /tmp/note.txt`.
In your notes, explain why the throwaway container could not find the note.
