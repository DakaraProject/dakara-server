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

### Added

- Alternative titles of a work : search songs and works upon the alternative title of a work.
- Reorder of the playlist

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
