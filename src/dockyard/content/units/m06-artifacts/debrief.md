## What you prevented

The fake `.env` no longer reaches any layer of your image, and the image matches your computer’s processor.
Preventing a file from entering the build is much safer than trying to delete it afterwards.

Check your understanding:
Why can a file deleted in a later Dockerfile step still be recovered from the image?
Name one thing this lesson’s checks do not tell you about the image’s safety.
