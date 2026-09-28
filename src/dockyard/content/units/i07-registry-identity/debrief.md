## Compare your diagnosis

The image existed and the registry was reachable; the Pod’s pull Secret still held the old password, so the registry rejected it.
A new `docker-registry` Secret for the exact registry address, with the current password, let fresh Pods pull the release.

Check your understanding:
Why did a successful `docker push` from your computer not prove the cluster could pull the image?
Which words in the pull error pointed at credentials rather than a missing image?
