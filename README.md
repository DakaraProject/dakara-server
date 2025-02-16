# Dakara server

<!-- Badges are displayed for the develop branch -->
[![Tests status](https://github.com/DakaraProject/dakara-server/actions/workflows/ci.yml/badge.svg)](https://github.com/DakaraProject/dakara-server/actions/workflows/ci.yml)
[![Codecov coverage analysis](https://codecov.io/gh/DakaraProject/dakara-server/branch/develop/graph/badge.svg)](https://codecov.io/gh/DakaraProject/dakara-server)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

Server for the Dakara project.

## Installation

To install Dakara completely, you have to get all the parts of the project.
Installation guidelines are provided here:

* [Dakara web client](https://github.com/DakaraProject/dakara-client-web/);
* [Dakara player VLC](https://github.com/DakaraProject/dakara-player-vlc/);
* [Dakara feeder](https://github.com/DakaraProject/dakara-feeder).

### System requirements

* Python3, to make everything up and running (supported versions: 3.9, 3.10, 3.11, and 3.12).

Linux, Mac and Windows are supported.

### Virtual environment

It is strongly recommended to run the Dakara server in a virtual environment.

### Dependencies

Install the package with:

<!-- ```sh -->
<!-- pip install dakaraserver -->
<!-- ``` -->
<!--  -->
<!-- If you have downloaded the repo, you can install the package directly with: -->

```sh
pip install .
```

## Setup

### Settings presets

The project provides settings presets: "development", "test", and "production".
By default, the development preset is used.

To select a preset, set the `DJANGO_SETTINGS_MODULE` environment variable accordingly, by instance for production:

```sh
export DJANGO_SETTINGS_MODULE="dakara_server.settings.production"
```

Note that with the development settings preset, the database is an SQLite file with the default name `db.sqlite3`, which is located in the current working directory.

### Using Django commands

The traditional Django `manage.py` command file is replaced by the `dakara-server` command line, which provides exactly the same features.

### Setting up the server

Let's create the server database, after loading the virtual environment, do:

```sh
dakara-server migrate
```

You should be asked to create a super user.
Do it.
Otherwise:

```sh
dakara-server createsuperuser
```

### Start the server

You're almost done! To start the server app, in the right virtual environment, do:

```sh
dakara-server runserver
```

The server part is now set up correctly.

### Web client, feeder and player

Now setup the [web client](https://github.com/DakaraProject/dakara-client-web), [feeder](https://github.com/DakaraProject/dakara-feeder) and [player](https://github.com/DakaraProject/dakara-player-vlc) according to their respective documentations.
The feeder can authenticate to the server using a token or a couple login/password of a playlist manager account.
The player can authenticate using a special token that only a playlist manager can generate.
Both tokens can be obtained from the web interface.

After all of this is setup, just grab some friends and have fun!

## Development

Please read the [developers documentation](CONTRIBUTING.md).
