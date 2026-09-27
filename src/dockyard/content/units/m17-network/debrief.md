# Debrief: Enforce network intent across nodes

The cross-node connection matrix demonstrates allowed and denied paths through an enforcing network plugin.
Testing both TCP and UDP DNS matters because restricting one transport can leave resolution failures that look intermittent.

## Explain your result

Which negative request proves the boundary is enforced, and which positive request proves you did not simply break all connectivity?

## Transfer beyond this lab

NetworkPolicy does not authenticate application users or automatically isolate every host-network path, so describe the tested scope precisely.
