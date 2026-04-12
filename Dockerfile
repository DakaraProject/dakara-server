FROM alpine:3.23

# if this variable is set to "dev", then the "dakara-client-web_dev.zip" file
# in the current working directory will be used
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

# copy dev front file if provided
COPY dakara-client-web_dev.zip* /tmp

# get the front archive
RUN FRONT_ARCHIVE="dakara-client-web_$FRONT_VERSION.zip" && \
    if [ -f "/tmp/$FRONT_ARCHIVE" ]; \
    then \
        echo "Using provided dev front archive"; \
    else \
        echo "Downloading front archive v$FRONT_VERSION" && \
        wget \
            -P /tmp \
            "https://github.com/DakaraProject/dakara-client-web/releases/download/$FRONT_VERSION/$FRONT_ARCHIVE"; \
    fi && \
    unzip \
        "/tmp/$FRONT_ARCHIVE" \
        -d /app && \
    rm -rf \
        "/tmp/$FRONT_ARCHIVE"

COPY deployment/etc/nginx/nginx.conf /etc/nginx/nginx.conf

COPY . /app

EXPOSE 80
VOLUME /data

# django settings
ENV DJANGO_SETTINGS_MODULE="dakara_server.settings.production"

# path
ENV PATH="$PATH:/app/deployment/bin"

WORKDIR /
