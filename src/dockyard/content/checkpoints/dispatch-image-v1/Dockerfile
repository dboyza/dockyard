ARG BASE_IMAGE
FROM ${BASE_IMAGE} AS verify
WORKDIR /source
COPY app.py VERSION ./
RUN python -m py_compile app.py
FROM ${BASE_IMAGE} AS runtime
WORKDIR /app
COPY --from=verify --chown=10001:10001 /source/app.py /source/VERSION ./
USER 10001:10001
EXPOSE 8080
CMD ["python", "app.py"]
