## Follow the packet, not the status

Both nodes were Ready the whole time; the dropped VXLAN packets only showed up in a firewall counter and in failed cross-node requests.

Check your understanding:
If a request to the Pod IP works but one to the Service name fails, which parts of the path have you already proved?
Why would flushing the whole firewall be a dangerous fix?
