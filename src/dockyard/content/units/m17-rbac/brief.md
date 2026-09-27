## Remove the extra permission

Your `dispatch-reader` account can currently read both Pods and Secrets.
It only needs to read Pods in the `dispatch` namespace.
Let’s narrow its access without breaking Dispatch.

1. Open `identity.yaml` and find the `dispatch-pod-reader` Role.
   Follow its RoleBinding to the `dispatch-reader` account used by the inventory Deployment.
2. Check the account’s Pod and Secret permissions with the `kubectl auth can-i` examples in Understand.
3. Edit the Role so it keeps Pod reads but cannot read Secrets or change resources.
   Keep the existing RoleBinding, inventory token, and token-free API and worker settings.
4. Apply the edited file with `python render.py identity.yaml | kubectl apply -f -`.
5. Repeat the three permission questions from Understand.
   Expect `yes` for Dispatch Pods, `no` for Secrets, and `no` for Pods in `kube-system`.
6. Choose **Check work** to test real token-authenticated requests and a complete Dispatch job.

Before moving on, explain why a successful request made as the administrator would not prove that the reader account works.
Also explain why a timeout is not the same as a forbidden response.
These explanations belong in your notes; the checker tests the permissions and application behavior.
