## Why was localhost wrong here?

The API made the request, so its localhost address referred to its own container.
The corrected setting names the peer on their shared network.

Explain which observation ruled out a missing DNS alias and which showed the configuration mistake.
If name lookup had failed too, what would you inspect before changing the URL again?
