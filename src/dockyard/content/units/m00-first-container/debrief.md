## What just happened?

Docker created a container from the Python image, started `python` inside it as the main process, and passed its output to your terminal.
When that process finished, the container stopped, but it was not deleted.
Its name, settings, exit code, and logs all stayed behind until you choose to remove it.

Check your understanding:
If you ran the same command again with a different name, how many containers would `docker ps -a` show, and how many images would they share?
Why did `docker ps` show nothing even though the container still existed?
If either answer feels uncertain, run `docker ps -a` again and look at the STATUS column.

The next lesson keeps a container running, makes a change inside it, and shows where that change is stored.
