Restore PostgreSQL using its original CSI claim and volume.
Correct the database workload's placement and recover any failed replacement Pod without deleting the PVC or PV.
The original volume handle, stored sentinel, and cluster identities must survive, and a fresh Dispatch job must complete.
Use Pod events, PVC/PV state, CSI registration, and attachment observations to explain the failure.
