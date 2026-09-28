# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure with backend/frontend separation
- Library service with SQLite + FTS5 search
- Playback service using python-vlc
- Queue service with repeat/shuffle modes
- Playlist service with CRUD operations
- Settings service with JSON persistence
- Frontend with PySide6 and dark burgundy glassmorphism theme
- Metadata extraction using mutagen (MP3, FLAC, OGG, M4A, WAV, AIFF)
- Artwork extraction and caching
- Library scanning with file system watching (watchdog)
- Comprehensive test suite with pytest

### Fixed
- Fixed deliberate crash in LibraryService.search() method

### Changed
- Updated README with comprehensive documentation
- Added MIT License
- Added CONTRIBUTING guidelines
- Added CHANGELOG

## [0.1.0] - 2024-09-28

### Added
- Initial release
- Basic music player functionality
- Library management (songs, albums, artists, genres)
- Audio playback with VLC
- Playback queue management
- Playlist creation and management
- Settings persistence
- Dark burgundy glassmorphism UI theme
- Search with FTS5 full-text search
- Cross-platform support (Windows, macOS, Linux)
- PyInstaller packaging for Windows executable

---

### Version History

| Version | Date | Description |
|---------|------|-------------|
| 0.1.0 | 2024-09-28 | Initial public release |