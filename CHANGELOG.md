# Changelog

<!---
## 0.0.1 - 1970-01-01

### Update notes

Any important notes regarding the update.

### Added

- New stuff.

### Changed

- Changed stuff.

### Deprecated

- Deprecated stuff.

### Removed

- Removed stuff.

### Fixed

- Fixed stuff.

### Security

- Security related fix.
-->

## Unreleased

## 1.8.1 - 2023-12-17

## 1.8.0 - 2022-11-23

### Update notes

The player does not need a special user any more to communicate with the server.
It is recommanded to delete this obsolete user from the database:

```python
python dakara_server/manage.py shell -c "from users.models import DakaraUser; DakaraUser.objects.filter(playlist_permission_level='p').delete()"
```

### Added

- Route for prune artists is `/api/library/artists/prune/` and route for prune works is `/api/library/works/prune/`.
- Tags, work types and works are now created with the feeder, using the routes `api/library/song-tags/`, `api/library/work-types/` and `api/library/works/` respectively.
- Player tokens are generated using the route `/api/playlist/player-token/`.
- Songs can be restarted, rewound, or fast forwarded during playback.
- Support Python 3.10 and 3.11.

### Changed

- The player is no longer treated as a special user.
  It can connect using a special player token that only a playlist manager can generate.

### Removed

- `prune` command.
  Prune for artists and works can be done through the API now.
- `createtags`, `createworktypes` and `createworks` commands.
  Creating tags, work types and works can be done through the API now.
- `createplayer` command and "player" as playlist permission level.
- Dropped support of Python 3.6.

## 1.7.0 - 2021-06-20

### Added

- Authentication by email is now possible, in addition to authentication by user name.
  This requires a working email server in production.
  Creating a new account can be done from the login page.
  In order to be functional, the account must have its email address validated (with a special link sent by email during account creation) and must be validated by an users manager (user managers are notified by email each time a new account is created).
  For production, this feature is enabled by default and can be disabled with the environment variable `EMAIL_ENABLED` set to `false`.
  This legacy configuration is designed for local servers, not exposed online.
  In this case the email address is automatically validated during account creation, but still has to be validated by an user manager.
  For development and testing, this feature is enabled, but a console email server and respectively a dummy email server are used instead.

### Changed

- The `createplayer` command accepts now `--username` and `--password` to respectively pass username and password.
  It also accepts `--noinput` to not prompt any input when calling the command.
- Authentication routes have been changed to `api/accounts/`:
    * Login: `api/token-auth/` -> `api/accounts/login/`, fields are now `login` and `password`;
    * Logout: `api/token-auth/logout/` -> `api/accounts/logout/`;
    * Change password: `api/users/<pk>/password/` -> `api/accounts/change-password/`.
- If emails are enabled, an user manager cannot change users password anymore.
- Route to get server version was changed to be more generic and to return settings: `api/version/` -> `api/settings/`.

### Removed

- Dropped support of Python 3.5.

## 1.6.0 - 2020-09-05

### Update notes

When updating Dakara server from 1.5 to 1.6, (which means updating Django from 1.11 to 2.2), the database may have inconstencies that lead to a crash when running `./manage.py runserver`.

To give more details, the database can contain invalid foreign key constraints.
The reason the problem occurs only with Django 2.0 is because with django 1, sqlite's foreign key constraints were not enforced, as explained in this [release note](https://docs.djangoproject.com/en/2.2/releases/2.0/#foreign-key-constraints-are-now-enabled-on-sqlite).
The actual reason why the database contains invalid foreign key constraints is due to a bug that was present when the database was created, as reported in this [ticket](https://code.djangoproject.com/ticket/29182) (note that the bug report initially stated that the bug does not occur when migrating using `./manage.py migrate` , but other comments reproduced the bug with it).
The bug has been fixed, but databases generated with Django 1 contains this bug.

To update the database and get rid of the bug, it is necessary to export, then reimport it using this procedure:

```sh
# starting from the project directory
cd dakara_server

# on dakara server v1.5, export parts of the database
./manage.py dumpdata library >db_library.json
./manage.py dumpdata users >db_users.json
./manage.py dumpdata playlist >db_playlist.json

# keep a backup of the database in case
mv db.squlite3 db_backup.sqlite3

# install the update, install dependencies

# now on dakara server 1.6, migrate
./manage.py migrate

# reimport the data
./manage.py loaddata db_library.json
./manage.py loaddata db_users.json
./manage.py loaddata db_playlist.json

# check everything is ok
./manage.py check
./manage.py runserver

# when you are sure that everything is ok, you can cleanup temporary and backup files
rm db_backup.sqlite3 db_library.json db_users.json db_playlist.json
```

### Added

- Add instrumental track support. New fields are `Song.has_instrumental` and `PlaylistEntry.use_instrumental`.

### Fixed

- Crash when updating a song with 2 works existing with same title but different subtitle.

## 1.5.1 - 2019-12-06

### Fixed

- Crash when 2 works exists with same title but different subtitle.

## 1.5.0 - 2019-12-05

### Added

- Route to retrieve path of all song in database. Used by the external feeder.

### Changed

- Song creation route now accepts a list of objects to create.
- Song creation route now accepts nested objects.

### Removed

- Feed Command. Feeding is now processed through external feeder. See dakara-feeder project.
- Replace directory command. Not needed anymore with the new feeder.

## 1.4.0 - 2019-05-03

### Changed

- Configuration is now split in `developement.py` for local use and `production.py` for server use.
  To override default values, set them in a `.env` file or `settings.ini` file.
- Kara status now consists of 3 booleans:
    * `ongoing`: When false, player does not play, nothing can be added to playlist. In this case, the two other booleans should are meaningless. Equivalent to the old `stop` status;
    * `can_add_to_playlist`: When false, users who are not playlist manager can't add songs to playlist;
    * `player_play_next_song`: When false, player finish playing current song if any, but does not play next song. Equivalent to the old `pause` status.

## 1.3.0 - 2018-10-07

### Added

- Alternative titles of a work : search songs and works upon the alternative title of a work.
- Reorder of the playlist
- Add createworks command : create works and their alternative titles upon a data structure file.
- Prevent to add a song to the playlist after a certain karaoke stop date.

### Changed

- Kara status is now handled within the Karaoke object.
- Karaoke route: `/playlist/kara-status/` > `/playlist/karaoke/`.
- Access to routes without authentication gives 401 HTTP error code instead of 403.

## 1.2.0 - 2018-06-03

### Added
- Kara status: global status to run, pause or stop the karaoke.
  - play: Same as previous behaviour.
  - pause: No additional song is played by the player. The player finishes playing current song.
  - stop: Player stops playing, playlist is emptied, can't add song to playlist.
- Kara status to digest route.
- Route `/playlist/played-entries/` to list played playlist entries with date played.
- Date when the entry is supposed to be played for playlist entries with `date_play`.
- End of playlist date with `date_end`.
- Limit to playlist size (default to 100 entries).
- Auto-generated documentation of the API: `/api-docs/`.

### Changed
- Playlist routes:
  - `/player/*` > `/playlist/device/*`
  - `/playlist/` > `/playlist/entries/`
  - `/playlist/<id>/` > `/playlist/entries/<id>/`
  - `/playlist/player/` > `/playlist/digest/`
- Digest route (old player route) content change:
  - `status` > `player_status`
  - `manage` > `player_manage`
  - `errors` > `player_errors`
- Attempting to delete playing playlist entry now returns 404 instead of 403.
- Pagination information (`current` and `last`) for views that use a paginator are now gathered in the `pagination` key in the response.
- Song serialization no longer contains the `link_type_name` key (work link long name), the info has to be deduced from `link_type`.
- In the route `/playlist/entries`, the key to designate a song has changed: `song` > `song_id`.
- Users are now listed by their user name.
- Song search now looks in song `version`, `detail` and `video_detail` fields.

## 1.1.0 - 2018-01-25

### Added
- New option for createtags and createworktypes commands: --prune, to remove tags and worktypes not in config file.
- New Command: prune, to remove works and artists no longer linked to a song.
- Allow to disable tags: song with disabled tags are visible only by the library manager and can be added to the playlist only by the playlist manager.

### Changed
- Song tags color now uses hue (`color_hue`) instead of id (`color_id`).

### Fixed
- When the feeder update a song, the song is no longer associated with old artists, works and tags.
- Only library manager can update library.

## 1.0.0 - 2017-11-12

### Added

- First version.
