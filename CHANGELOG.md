# Changelog

<!---
## 0.0.1 - 1970-01-01

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
