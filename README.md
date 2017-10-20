# Dakara server

Server for the Dakara project.

### Installation

To install Dakara completely, you have to get all the parts of the project.
Installation guidelines are provided over here:

* [Dakara web client](https://github.com/Nadeflore/dakara-client-web/);
* [Dakara player VLC](https://github.com/Nadeflore/dakara-player-vlc/).

#### System requirements

* Python3, to make everything up and running;
* [ffmpeg](https://www.ffmpeg.org/), to extract lyrics and extract metadata from files (preferred way);
* [MediaInfo](https://mediaarea.net/fr/MediaInfo/), to extract metadata from files (slower, alternative way, may not work on Windows).

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

Now, duplicate `config.yaml.example` to `config.yaml`.
You'll set up here the different tags and type of works (anime, games…) of your kara library.
When you're done, tell the server:

```sh
dakara_server/manage.py createtags ./config.yaml # for tags
dakara_server/manage.py createworktypes ./config.yaml # for work types
```

It's time to feed the hungry database with your kara library!
Suppose you have only one kara folder with all your files inside, you simply call the feeder this way:

```sh
dakara_server/manage.py feed path/to/kara
```

Suppose now you have an anime songs folder and a Jpop songs folder in a parent kara folder.
The files are located in those two subdirectories:

```
kara
|-- anime
`-- jpop
```

You simply feed the database this way:

```sh
dakara_server/manage.py feed path/to/kara --directory anime
dakara_server/manage.py feed path/to/kara --directory jpop
```

In this case, all imported files will have a path relative to the parent folder.
When setting up the Dakara player, you shall specify the path of this kara folder.

This may take some time, depending of your collection.
You'll need `ffprobe`, provided by Ffmpeg, for this process to extract files duration (which is slow).
You'll need `ffmpeg` as well to extract embedded lyrics from files.
Pass the `-h` parameter to get some help and all the options of the feeder.

Build and link the dist folder from the [client](https://github.com/Nadeflore/dakara-client-web) to `dakara_server/static`.

Setup the [player](https://github.com/Nadeflore/dakara-player-vlc/) accordingly.

### Start the server

You're almost done! To start the server app, in the right virtual environment, do:

```
dakara_server/manage.py runserver
```

Don't forget to start the player as well.

Now, just grab some friends and have fun!

### Development

#### Hooks

Git hooks are included in the `hooks` directory.

Use the following command to use this hook folder for the project:

```
git config core.hooksPath hooks
```

If you're using git < 2.9 you can make a symlink instead:

```
ln -s -f ../../hooks/pre-commit .git/hooks/pre-commit
```
