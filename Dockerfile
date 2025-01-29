FROM python:3-alpine

# hadolint ignore=DL3018
RUN apk add --virtual deps --no-cache git gcc musl-dev && \
    pip install --no-cache-dir git+https://github.com/pschmitt/aiovodafone@cli && \
    apk del deps

ENTRYPOINT ["vodafone-cli"]
