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
- Kara status: global status to run, pause or stop the karaoke.
  - play: Same as previous behaviour.
  - pause: No additional song is played by the player. The player finishes playing current song.
  - stop: Player stops playing, playlist is emptied, can't add song to playlist.

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
