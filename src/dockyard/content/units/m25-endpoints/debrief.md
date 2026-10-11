## What changed

Every Pod in `frontend` is now selected by an egress policy that allows only DNS and the Dispatch API.
Requests to the metadata address and to the kubelets match no rule, so they are dropped before they leave the Pod, while the trusted client's jobs still flow.

Check your understanding: a new Pod added to `frontend` next week needs to call an external payment service.
What must change, and what stays protected?
Why would writing the namespace and Pod selectors as two separate list items have weakened the Dispatch rule?
