ARG BASE_IMAGE
FROM ${BASE_IMAGE} AS dependencies
WORKDIR /build
COPY requirements.txt ./
RUN python -m pip download --require-hashes --only-binary=:all: -r requirements.txt -d /wheels
FROM ${BASE_IMAGE} AS runtime
COPY --from=dependencies /wheels /wheels
COPY requirements.txt /wheels/requirements.txt
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels --require-hashes -r /wheels/requirements.txt && rm -rf /wheels
ARG INCLUDE_LEGACY=true
COPY --from=fixture PyJWT-1.7.1-py2.py3-none-any.whl /tmp/fixture/
RUN if [ "$INCLUDE_LEGACY" = true ]; then python -m pip install --no-index --no-deps /tmp/fixture/PyJWT-1.7.1-py2.py3-none-any.whl; fi && rm -rf /tmp/fixture
WORKDIR /app
COPY --chown=10001:10001 --chmod=0644 app.py database.py worker.py maintenance.py dashboard.html VERSION ./
USER 10001:10001
EXPOSE 8080
CMD ["python", "app.py"]
