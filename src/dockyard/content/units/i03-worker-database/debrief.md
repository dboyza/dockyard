## Compare your diagnosis

The workers had their own `DB_NAME` setting pointing at a database that did not exist, while the API used the correct one.
Both services ran the same image, so the difference was entirely in their settings.
The API’s readiness check only tested the API’s own connections, which is why it stayed green.
Fixing the worker’s setting brought processing back without touching stored data or opening up the database.

Check your understanding:
Which log line pointed you at the worker’s settings?
What could a team monitor to notice this sooner, such as the number of jobs waiting and how long they have waited?
