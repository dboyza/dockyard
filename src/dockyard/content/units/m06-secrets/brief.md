## Sign the release without recording the token

Dispatch's build signs each release with a token, but the token is visible to anyone who reads the image's history.

1. Find the token in `docker image history --no-trunc` for the running image.
2. Change the `Dockerfile` to read the token from a BuildKit secret mount instead of a build argument.
3. Change `release.sh` to pass `release-token.txt` with `--secret`, rebuild, and replace the container.
4. Confirm the history no longer shows the token and the image still has a valid `SIGNATURE`, then choose **Check work**.

Keep `release-token.txt` in your workspace and out of the image.
In your notes, explain why deleting the `ARG` line alone would not have been a complete fix.
