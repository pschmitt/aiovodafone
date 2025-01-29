FROM python:3-alpine

# hadolint ignore=DL3018
RUN apk add --no-cache git && \
    pip install --no-cache-dir git+https://github.com/pschmitt/aiovodafone@cli && \
    apk del git

ENTRYPOINT ["vodafone-cli"]
