## A broken client, a healthy cluster

The control plane was fine all along; the operator client was aimed at the wrong place.
Reading the error category first pointed you at the client rather than the cluster.

Check your understanding:
Which error would you expect for each of: wrong address, untrusted certificate, wrong password, and missing permission?
Why must a kubeconfig containing a client key be mode 600?
