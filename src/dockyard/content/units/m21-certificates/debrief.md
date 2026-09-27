# Debrief: Renew and verify the certificate clients actually receive

The renewed certificate is checked through the TLS connection that a client actually receives, under the original trusted CA.
A changed certificate file alone would not prove that the serving API process has loaded it.

## Explain your result

Which observations separate renewed on-disk material, the served leaf certificate, and preserved trust in the original cluster?

## Transfer beyond this lab

Certificate rotation needs a rollout or reload plan for consumers as well as expiry monitoring and recoverable access to the appropriate signing authority.
