## Compare your diagnosis

The release added an extra key to the Service’s selector that no Pod had, so the Service matched nothing even though every Pod was healthy.
You could fix it either by removing that stale key from the selector or by adding the label to the Pods, as long as the Service ends up selecting exactly the Dispatch API Pods.

Check your understanding:
Which command showed you the problem most directly?
Why would restarting the database, or the API Pods, have changed nothing?
