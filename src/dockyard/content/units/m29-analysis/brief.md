## Pass a static analysis gate

The `resizer` manifest went to production without review.

1. Run KubeLinter and kubesec on the rendered `resizer.yaml`, and read every finding.
2. Fix the manifest until KubeLinter reports no errors and kubesec scores the Deployment at least 10 with no critical findings.
3. Deploy it with `sh run.sh`, confirm the resizer still makes thumbnails, and choose **Check work**.

Dispatch must keep processing jobs.
In your notes, list one piece of analyser advice you chose not to follow, if any, and explain why.
