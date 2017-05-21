# Dakara server

Server for the Dakara project.

### Installation

To install Dakara completely, you have to get all the parts of the project.
Installation guidelines are provided over here:

* [Dakara web client](https://github.com/Nadeflore/dakara-client-web/);
* [Dakara player VLC](https://github.com/Nadeflore/dakara-player-vlc/).

#### System requirements

* Python3, to make everything up and running;
* [MediaInfo](https://mediaarea.net/fr/MediaInfo/), to extract metadata from files.

#### Virtual environment

It is strongly recommended to run Dakara server on virtual environment.

#### Python dependencies

Install dependencies, at root level of the repo:

```
pip install -r requirements.txt
```

#### Setting up the server and feeding the database

Let's create the server database, in `dakara_server`, do:

```
python manage.py syncdb
```

Grab some files for your kara library, in `tools`, do:

```
python feed_database.py /path/to/your/songs
```

You'll need MediaInfo for this process.
Pass the `-h` option to get some help for this command.

Link the dist folder from [Dakara web client](https://github.com/Nadeflore/dakara-client-web) to `dakara_server/static`.

### Start the server

You're almost done! To start the server app, in the right virtual environment and in `dakara_server`, do:

```
python manage.py runserver
```

It's time to run the player.
In the right virtual environment and in the right place, do:

```
python kara.py
```

Now, just grab some friends and have fun!
