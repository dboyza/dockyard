## What just happened?

Your note went into your container’s own writable layer, on top of the shared, read-only image layers.
`docker diff` showed exactly that change, and a fresh container made from the same image started without it.

Check your understanding:
If you removed this container and created a new one with the same name, would `/tmp/note.txt` still be there?
Why is it safe for a hundred containers to share one image?
Where would you keep data that must survive the container being replaced?
You’ll meet a proper answer to that last question in a later module.

The next lesson runs a program that waits for requests, connects it to your computer, and shares a folder of files with it.
