FROM alpine:3.23

# the front archive name must be in the format "dakara-client-web_<FRONT_VERSION>.zip"
# any front archive in the current build directory will be directly copied in
# the image, and will be used if the version number corresponds to the one
# requested below
# otherwise, the front archive will be downloaded
ARG FRONT_VERSION

# optimizations for Python and pip
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV AUTOBAHN_USE_NVX=0

RUN apk add --no-cache \
        nginx \
        py3-pip \
        python3 \
        unzip \
        wget

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

EXPOSE 80
VOLUME /data

# django settings
ENV DJANGO_SETTINGS_MODULE="dakara_server.settings.production"

# path
ENV PATH="$PATH:/app/deployment/scripts"

WORKDIR /
