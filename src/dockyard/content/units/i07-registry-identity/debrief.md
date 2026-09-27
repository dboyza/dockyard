# Recovery review

The registry accepted the build-time publishing identity, but the workload Secret retained an expired credential.
A correct repair places the current identity under the exact registry authority in a namespaced image-pull Secret.
Anonymous requests remain rejected, and a fresh Pod using the repaired identity resolves and executes the private release.
The actual API and worker path then demonstrates that pulling the image was necessary but not sufficient for application recovery.
Explain why a successful docker push from the host did not establish the Pod's pull authority.
