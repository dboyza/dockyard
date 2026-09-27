# Debrief: Initialize a control plane from prepared Linux guests

Initialization establishes the native API and the four primary static control-plane components on prepared Linux guests.
It does not by itself establish a joined worker, working Pod networking, or a complete Dispatch transaction.

## Explain your result

Explain which state kubeadm created, which process the kubelet now supervises, and which observations remain necessary before scheduling application work.

## Transfer beyond this lab

Treat bootstrap configuration, certificates, and cluster identity as persistent operational state rather than disposable command output.
