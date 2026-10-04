ARG BASE_IMAGE
FROM ${BASE_IMAGE}
WORKDIR /app
COPY app.py VERSION sign.py ./
RUN --mount=type=secret,id=release_token,required=true python sign.py < /run/secrets/release_token > SIGNATURE
CMD ["python", "app.py"]
