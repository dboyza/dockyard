ARG BASE_IMAGE
FROM ${BASE_IMAGE}
WORKDIR /app
COPY --chown=10001:10001 app.py VERSION ./
# Remove what the application never needs at runtime: setuid privileges, package
# installers, and BusyBox, which every shell links to. The shell running this step is
# BusyBox too, and keeps working until the step ends.
RUN find / -xdev -type f -perm /6000 -exec chmod a-s {} + \
 && rm -rf /sbin/apk /etc/apk /lib/apk /usr/local/bin/pip* \
 && rm /bin/busybox
USER 10001:10001
# Exec form: Docker starts Python directly, so no shell is needed.
CMD ["python", "app.py"]
