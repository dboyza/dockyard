## What changed

The API server now encrypts Secrets with AES before storing them, and every existing Secret was rewritten through the new provider, so etcd and its backups hold ciphertext.
Applications noticed nothing, because the API server decrypts on the way out.

Check your understanding: the key sits in a file on the control-plane node.
Who can still read your Secrets, and why do production clusters move the key into a KMS?
How would you rotate to a new key without making any Secret unreadable along the way?
