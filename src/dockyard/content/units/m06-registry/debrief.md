## Why deploy by digest?

Your container now names an exact image by its fingerprint.
Even if someone pushes a different image under the `release` tag, this container, and any new one created from the same reference, keeps running the content you tested.

Check your understanding:
What would change, and what would stay the same, if a colleague pushed a new build as `dispatch:release` right now?
Why did you still need a `/healthz` request after a successful push?
