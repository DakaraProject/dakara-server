# Dakara server

[![Travis CI Build Status](https://travis-ci.com/DakaraProject/dakara-server.svg?branch=develop)](https://travis-ci.com/DakaraProject/dakara-server)
[![Appveyor CI Build status](https://ci.appveyor.com/api/projects/status/2wdia71y3dwsqywp?svg=true)](https://ci.appveyor.com/project/neraste/dakara-server)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

Server for the Dakara project.

### Installation

To install Dakara completely, you have to get all the parts of the project.
Installation guidelines are provided over here:

* [Dakara web client](https://github.com/DakaraProject/dakara-client-web/);
* [Dakara player VLC](https://github.com/DakaraProject/dakara-player-vlc/).

#### System requirements

* Python3, to make everything up and running (supported versions: 3.5 and 3.6);
* [ffmpeg](https://www.ffmpeg.org/), to extract lyrics and extract metadata from files (preferred way);
* [MediaInfo](https://mediaarea.net/fr/MediaInfo/), to extract metadata from files (slower, alternative way, may not work on Windows).

Linux and Windows are supported.

#### Virtual environment

It is strongly recommended to run the Dakara server in a virtual environment.

#### Python dependencies

Install dependencies, at the root level of the repo (in the virtual environment):

```
pip install -r requirements.txt
```

#### Setting up the server and feeding the database

Let's create the server database, after loading the virtual environment, do:

```
dakara_server/manage.py migrate
```

You should be asked to create a super user. Do it. Otherwise:

```
dakara_server/manage.py createsuperuser
```

You should also create a player user:

```
dakara_server/manage.py createplayer
```

Now, duplicate `config.yaml.example` to `config.yaml`.
You'll set up here the different tags and type of works (anime, games…) of your kara library.
When you're done, tell the server:

```sh
dakara_server/manage.py createtags ./config.yaml # for tags
dakara_server/manage.py createworktypes ./config.yaml # for work types
```

Build and link the dist folder from the [client](https://github.com/DakaraProject/dakara-client-web) to `dakara_server/static`.

### Start the server

You're almost done! To start the server app, in the right virtual environment, do:

```
dakara_server/manage.py runserver
```

The server part is now setup correctly.

### Feeder and player

Now setup the [feeder](https://github.com/DakaraProject/dakara-feeder) and [player](https://github.com/DakaraProject/dakara-player-vlc) accroding to their respective documentations.

After all of this is setup, just grab some friends and have fun!

### Development

#### Tests

Tests are written using either Unittest or Pytest.
Pytest is used to run all tests, regardless the test framework used:

```
pytest
```

#### Hooks

Git hooks are included in the `hooks` directory.

Use the following command to use this hook folder for the project:

```
git config core.hooksPath hooks
```

If you're using git < 2.9 you can make a symlink instead:

```
ln -s -f ../../hooks/pre-commit .git/hooks/pre-commit
ln -s -f ../../hooks/pre-commit.d .git/hooks/pre-commit.d
```

#### Code style

The code follows the [PEP8](https://www.python.org/dev/peps/pep-0008/) style guide (88 chars per line).
Quality of code is checked with [Flake8](https://pypi.org/project/flake8/).
Style is enforced using [Black](https://github.com/ambv/black).
You need to call Black before committing changes.
You may want to configure your editor to call it automatically.
Additionnal checking can be manually performed with [Pylint](https://www.pylint.org/).
