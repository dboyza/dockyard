## Renew the API server’s certificate

1. Record the API server certificate’s serial number and issuer.
2. Renew it with `kubeadm certs renew apiserver`, and confirm the serial changed and the issuer did not.
3. Restart the API server container so it serves the new certificate, and wait for `kubectl get --raw=/readyz`.
4. Choose **Check work**.

Do not turn off certificate verification or replace the CA.
The cluster and its data must stay intact, and a new job must complete.
In your notes, explain why seeing the new certificate file is not enough on its own.
