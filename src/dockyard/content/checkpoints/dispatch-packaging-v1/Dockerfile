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
COPY --chown=10001:10001 --chmod=0644 app.py database.py worker.py maintenance.py workerpool_controller.py dashboard.html VERSION ./
USER 10001:10001
EXPOSE 8080
CMD ["python", "app.py"]
