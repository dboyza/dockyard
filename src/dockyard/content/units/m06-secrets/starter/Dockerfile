ARG BASE_IMAGE
FROM ${BASE_IMAGE}
WORKDIR /app
COPY app.py VERSION sign.py ./
ARG RELEASE_TOKEN
RUN echo "$RELEASE_TOKEN" | python sign.py > SIGNATURE
CMD ["python", "app.py"]
