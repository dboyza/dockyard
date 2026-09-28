## Same name, same storage, new Pod

`db-0` came back with the same name and claim but a new UID, and the data was still there.
The Retain policy means scaling down or deleting the StatefulSet would no longer throw that claim away.

Check your understanding:
What is the difference between the StatefulSet’s claim retention policy and a PV’s reclaim policy?
Why would scaling this StatefulSet to three not give you a replicated database?
