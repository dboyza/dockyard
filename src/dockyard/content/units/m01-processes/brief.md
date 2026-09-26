Run the supplied Dispatch API in a container and make it reachable from this Mac.

1. Prepare the lab and open its dedicated WezTerm tab.
2. Inspect `app.py`, then start it using the Python image and the assigned container name, label, and loopback port.
3. Request `/healthz` and inspect the application logs.
4. Stop the container, observe a failed request, and start the same container again.
5. Leave the API running and choose **Check work**.

The required result is a running lab-owned container whose published endpoint returns the Dispatch health response.
You can use the worked example for this guided lesson.
Later missions will ask for the same outcomes without a complete command sequence.
