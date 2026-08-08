# Dakara server

<!-- Badges are displayed for the develop branch -->
[]![Docker Image Version](https://img.shields.io/docker/v/dakaraproject/dakaraserver)](https://hub.docker.com/r/dakaraproject/dakaraserver)
[![Python versions](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue)](https://github.com/DakaraProject/dakara-server)
[![License](https://img.shields.io/github/license/mashape/apistatus.svg)](https://github.com/DakaraProject/dakara-server?tab=MIT-1-ov-file#readme)
[![Tests status](https://github.com/DakaraProject/dakara-server/actions/workflows/ci.yml/badge.svg)](https://github.com/DakaraProject/dakara-server/actions/workflows/ci.yml)
[![Codecov coverage analysis](https://codecov.io/gh/DakaraProject/dakara-server/branch/develop/graph/badge.svg)](https://codecov.io/gh/DakaraProject/dakara-server)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

Server for the Dakara project.

## Local installation

To install Dakara completely, you have to get all the parts of the project.
Installation guidelines are provided here:

* [Dakara web client](https://github.com/DakaraProject/dakara-client-web/) (you may not require it, see below);
* [Dakara player VLC](https://github.com/DakaraProject/dakara-player-vlc/);
* [Dakara feeder](https://github.com/DakaraProject/dakara-feeder).

### System requirements

* Python3, to make everything up and running (supported versions: see above).

Linux, Mac and Windows are supported.

### Virtual environment

It is strongly recommended to run the Dakara server in a virtual environment.

```sh
python -m virtualenv venv
source venv/bin/activate
```

### Dependencies

Having a recent enough versio of `pip` is required to install some dependencies properly:

```sh
pip install --upgrade pip
```

Install dependencies, at the root level of the repo (in the virtual environment):

```sh
pip install -r requirements.txt
```

For production, you will need some extra dependencies:

```sh
pip install -r requirements_prod.txt
```

## Setup

### Settings presets

The project provides settings presets:

- "development": for development purpose only. Uses a SQLite database, has debug mode enabled, an in-terminal pseudo mail backend, and security features turned off. Do not use this preset for production!
- "test": for test purpose only. Uses an in-memory SQLite database, and has security features turned off. Do not use this preset for production!
- "production": for use in the provided Docker image.

By default, the development preset is used.

You can create your own settings preset by duplicating the production file.

To select a preset, set the `DJANGO_SETTINGS_MODULE` environment variable accordingly, by instance for production:


```sh
export DJANGO_SETTINGS_MODULE="dakara_server.settings.production"
```

### Preparation of the server

Running the server in development requires some preliminary steps.

Let's create the server database, after loading the virtual environment, do:

```sh
dakara_server/manage.py migrate
```

You should be asked to create a super user.
Do it.
Otherwise:

```sh
dakara_server/manage.py createsuperuser
```

### Start the server

You're almost done! To start the server app, in the right virtual environment, do:

```sh
dakara_server/manage.py runserver
```

In a separate terminal, also run the scheduler.
This is currently only required for the kara date stop feature (which stops the karaoke at a certain date):

```sh
dakara_server/manage.py runapscheduler
```

The server part is now set up correctly.

### Web client, feeder and player

Now setup the [web client](https://github.com/DakaraProject/dakara-client-web), [feeder](https://github.com/DakaraProject/dakara-feeder) and [player](https://github.com/DakaraProject/dakara-player-vlc) according to their respective documentations.
The feeder can authenticate to the server using a token or a couple login/password of a playlist manager account.
The player can authenticate using a special token that only a playlist manager can generate.
Both tokens can be obtained from the web interface.

After all of this is setup, just grab some friends and have fun!

## Docker image

For production, it is recommended to use the provided Docker image, which takes care of all the aspects of the execution.

### How to get it

You can pull the image from Docker hub:

```sh
docker pull dakaraproject/dakaraserver:latest
```

Alternatively, you can also build the image locally with:

```sh
sudo docker build . -t dakaraserver
```

### Run manually

Run the container with:

```sh
sudo docker run \
         -d \
         -v path/to/persistent/data:/data \
         -e DAKARA_DATABASE_URL="mysql://user:password@mysql/dakara" \
         -e DAKARA_REDIS_URL="redis://redis:6379" \
         -e DAKARA_ALLOWED_HOSTS="localhost,example.com" \
         -e DAKARA_HOST_URL="http://example.com" \
         -e DAKARA_CSRF_TRUSTED_ORIGINS: "http://example.com" \
         -e DAKARA_SECRET_KEY="your-secret-key" \
         -e DAKARA_SUPERUSER_PASSWORD: "admin-password" \
         -e DAKARA_EMAIL_ENABLED=<true or false> \
         -e DAKARA_EMAIL_URL="smtp://user:password@postfix:25" \
         -e DAKARA_SENDER_EMAIL="no-reply@example.com" \
         -e DAKARA_LOG_TO_CONSOLE: false \
         -p 80:80 \
         dakaraserver \
         <command>
```

with `<command>` being either `run_daphne.sh`, `run_gunicorn.sh`, `run_apscheduler.sh`, or `run_nginx.sh`.
You need to have all of them running to have a workable instance of the server.
Running the container for the different services manually like this should be reserved for debugging or testing.
For production, it is advised to use Docker compose.

### Run with Docker compose

Docker compose is the preffered way to run an instance of the server, especially for production.
A sample `docker-compose.yaml` file is given in `deployment/docker-compose/docker-compose.yaml`.

```sh
cp deployment/docker-compose/docker-compose.yaml ./
# edit it as you like
# then start it
sudo docker compose up -d
```

Finally, use your browser to acces the web client:

```sh
xdg-open http://localhost
```

## Development

Please read the [developers documentation](CONTRIBUTING.md).
