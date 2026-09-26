## Remove the context leak

Prepare builds and starts an image whose broad COPY includes the supplied fake .env file.
Repair the build context or explicit copy selection so that file never enters a layer of the final application image.
Build explicitly for `linux/arm64`, then replace the API container with the corrected image.
Do not solve the leak by copying and later deleting the file.

Preserve the application release and endpoint contract.
Leave the fake .env in the workspace as evidence of the excluded input, and inspect the shipped image's platform.
