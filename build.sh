#!/usr/bin/env sh

    # -e "DEPS=libsasl2-dev libssl-dev libldap2-dev" \

docker run -it --rm --net=host \
    --platform linux/arm/v7 \
    -v "$PWD:/app" \
    -e REQUIREMENTS_FILE=requirements.txt \
    pschmitt/pyinstaller:3.10 \
    --hidden-import=pkg_resources.py2_warn \
        src/aiovodafone/cli.py
