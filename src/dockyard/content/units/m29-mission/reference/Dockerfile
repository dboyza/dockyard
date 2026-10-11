ARG BASE_IMAGE
FROM ${BASE_IMAGE} AS dependencies
WORKDIR /build
COPY requirements.txt ./
RUN python -m pip download --require-hashes --only-binary=:all: -r requirements.txt -d /wheels
FROM ${BASE_IMAGE} AS runtime
COPY --from=dependencies /wheels /wheels
COPY requirements.txt /wheels/requirements.txt
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels --require-hashes -r /wheels/requirements.txt && rm -rf /wheels
WORKDIR /app
COPY --chown=10001:10001 --chmod=0644 app.py database.py worker.py maintenance.py dashboard.html VERSION ./
# Strip what the runtime never needs. Every shell here links to BusyBox, and the shell
# running this step keeps working until it ends.
RUN find / -xdev -type f -perm /6000 -exec chmod a-s {} + \
 && rm -rf /sbin/apk /etc/apk /lib/apk /usr/local/bin/pip* \
 && rm /bin/busybox
USER 10001:10001
EXPOSE 8080
CMD ["python", "app.py"]
