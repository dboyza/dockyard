ARG BASE_IMAGE
FROM ${BASE_IMAGE}
WORKDIR /app
COPY --chmod=0644 app.py launch.sh ./
CMD ["sh", "/app/launch.sh"]
