## From Secret to working connection

The Secret existed the whole time.
What was broken was the path from it to the application: the key name in the volume.
Once the file appeared, the API could log in to PostgreSQL.

Check your understanding:
Why does base64 not protect a password from someone allowed to read the Secret?
Name two places a password could accidentally leak while you are troubleshooting.
