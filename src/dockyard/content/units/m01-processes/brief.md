Let’s get Dispatch answering a request from your computer.
Use the commands in Understand as you work through these steps.

1. Prepare the lab and open its dedicated lab terminal session.
2. Start the supplied `app.py` using the command in Understand.
   Keep the assigned name, lab label, and local port mapping.
3. Request `/healthz` and inspect the application logs.
4. Stop the container, observe a failed request, and start the same container again.
5. Leave the API running and choose **Check work**.

You’re ready to check when your container is running and `/healthz` returns `service: dispatch`.
In your notes, explain why the request failed while the container was stopped even though its image was still there.
You can use the worked example for this guided lesson.
Later missions will ask for the same outcomes without a complete command sequence.
