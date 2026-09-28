## Start a canary and a preview route

1. Look at the canary Deployment’s replica count and the preview Service’s selector.
2. In `canary.yaml`, run one candidate replica. In `preview.yaml`, make the Service select only `track=canary`.
3. Keep two stable replicas and leave the main `dispatch` Service selecting `app=dispatch`, so it reaches all three Pods.
4. Run `sh run.sh`, then check both Services’ endpoints and the release each one returns.
5. Choose **Check work**.

Do not change the stable Deployment’s selector or image.
In your notes, explain how you would promote or abort this release, and why two-to-one Pods is not an exact traffic split.
