## Restore the ability to save jobs

Compare the API’s user and group numbers with the owner and permissions of `/data`.
Repair ownership of the assigned volume so user 10001 can write there.
Keep the API running without root privileges and preserve the existing volume.

Check a new job submission and read it back through `/jobs`.
Explain why another image build would not repair the existing volume’s owner.
