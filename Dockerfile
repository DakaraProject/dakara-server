FROM alpine:3.23

# the front archive name must be in the format "dakara-client-web_<FRONT_VERSION>.zip"
# any front archive in the current build directory will be directly copied in
# the image, and will be used if the version number corresponds to the one
# requested below
# otherwise, the front archive will be downloaded
ARG FRONT_VERSION

# optimizations for Python and pip
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    AUTOBAHN_USE_NVX=0

RUN apk add --no-cache \
        "nginx=1.28.3-r7" \
        "py3-pip=25.1.1-r1" \
        "python3=3.12.13-r0" \
        "sudo=1.9.17_p2-r0" \
        "unzip=6.0-r16" \
        "wget=1.25.0-r2"

# install dependencies
RUN --mount=source=requirements.txt,target=/requirements.txt \
    --mount=source=requirements_prod.txt,target=/requirements_prod.txt \
    pip install \
        --no-cache-dir \
        --root-user-action ignore \
        --break-system-packages \
        -r /requirements.txt \
        -r /requirements_prod.txt

COPY . /app

# get the front archive
RUN if [ -z "$FRONT_VERSION" ]; \
    then \
        echo "Error: FRONT_VERSION is not set"; \
        exit 1; \
    fi && \
    FRONT_ARCHIVE="dakara-client-web_$FRONT_VERSION.zip" && \
    if [ -f "/app/$FRONT_ARCHIVE" ]; \
    then \
        echo "Using provided dev front archive" && \
        mv "/app/$FRONT_ARCHIVE" "/tmp/$FRONT_ARCHIVE"; \
    else \
        echo "Downloading front archive v$FRONT_VERSION" && \
        wget \
            -q \
            -P /tmp \
            "https://github.com/DakaraProject/dakara-client-web/releases/download/$FRONT_VERSION/$FRONT_ARCHIVE"; \
    fi && \
    unzip \
        "/tmp/$FRONT_ARCHIVE" \
        -d /app && \
    rm \
        -f \
        "/tmp/$FRONT_ARCHIVE" && \
    find \
        /app \
        -name "dakara-client-web_*" \
        -delete

COPY deployment/etc/nginx/nginx.conf /etc/nginx/nginx.conf

# create user
RUN addgroup -S appgroup && \
    adduser -S appuser -G appgroup

# give enough rights to user
RUN chown -R appuser:appgroup \
        /app \
        /var/lib/nginx \
        /var/log/nginx \
        /var/run/nginx

EXPOSE 80
VOLUME /data

# django settings and path
ENV DJANGO_SETTINGS_MODULE="dakara_server.settings.production" \
    PATH="$PATH:/app/deployment/scripts"

WORKDIR /

ENTRYPOINT ["/bin/sh", "/app/deployment/scripts/run_entrypoint.sh"]
