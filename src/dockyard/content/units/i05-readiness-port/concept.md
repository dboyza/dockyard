# Diagnostic approach

Named probe ports are resolved inside the Pod.
The Service port, target port, container port name, and the process listener describe related but separate boundaries.
A successful startup probe permits later probes to run; it cannot guarantee that readiness targets the same listener.
For a separate example, an admin process on 9001 can pass startup while a readiness probe accidentally targets a metrics port on 9002.
Compare the HTTP connection error with the actual listener before changing dependency credentials.
During this incident, use Pod events and a direct process request to decide whether the failure is application initialization, dependency availability, or probe routing.
