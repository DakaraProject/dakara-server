FROM alpine:3.23

# the front archive name must be in the format "dakara-client-web_<FRONT_VERSION>.zip"
# any front archive in the current build directory will be directly copied in
# the image, and will be used if the version number corresponds to the one
# requested below
# otherwise, the front archive will be downloaded
ARG FRONT_VERSION="1.9.2"

# optimizations for Python and pip
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apk add --no-cache \
        nginx \
        py3-pip \
        python3 \
        unzip \
        wget

COPY requirements.txt requirements_prod.txt /app/

# install dependencies
RUN pip install \
        --no-cache-dir \
        --root-user-action ignore \
        --break-system-packages \
        -r /app/requirements.txt \
        -r /app/requirements_prod.txt

COPY . /app

# get the front archive
RUN FRONT_ARCHIVE="dakara-client-web_$FRONT_VERSION.zip" && \
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
ENV PATH="$PATH:/app/deployment/bin"

WORKDIR /
