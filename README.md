# Music Player

A modern, cross-platform desktop music player built with Python, PySide6 (Qt6), and SQLite. Features a beautiful dark burgundy glassmorphism UI, full library management, playlists, queue, and high-quality audio playback via VLC.

## Features

- **Library Management**: Scan and organize your music collection (MP3, FLAC, OGG, M4A, WAV, AIFF)
- **Rich Metadata**: Automatic extraction of tags, artwork, and audio properties using mutagen
- **Full-Text Search**: Fast FTS5-powered search across songs, albums, and artists
- **Playback**: High-quality audio via python-vlc with gapless playback support
- **Queue & Playback Controls**: Play, pause, seek, volume, shuffle, repeat (off/one/all)
- **Playlists**: Create, edit, reorder, and manage custom playlists
- **Smart Views**: Browse by Songs, Albums, Artists, Genres with filtering
- **Settings**: Persistent configuration (library paths, theme, tray behavior, etc.)
- **System Tray**: Minimize to tray, global hotkeys (planned)
- **Cross-Platform**: Windows, macOS, Linux support
- **Packaging**: Ready-to-distribute Windows executable via PyInstaller

## Screenshots

*Coming soon - the UI features a stunning dark burgundy glassmorphism theme with subtle particle effects*

## Quick Start

### Prerequisites

- **Python 3.11+** ([Download](https://python.org/downloads))
- **VLC Media Player** ([Download](https://www.videolan.org/vlc/)) - Required for audio playback
- **Git** ([Download](https://git-scm.com/))

### Installation

```bash
# Clone the repository
git clone https://github.com/deeptech760-stack/music-player.git
cd music-player

# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### Running the Application

```bash
# Development run
python -m src.main

# Or use convenience scripts
# Windows:
run.bat
# macOS/Linux:
chmod +x run.sh
./run.sh
```

On first launch, you'll be prompted to select your music library folders. The app will scan and index your music automatically.

## Building Windows Executable

```bash
# Install PyInstaller (already in requirements.txt)
pip install pyinstaller

# Build
pyinstaller --clean MusicPlayer.spec

# Output: dist/MusicPlayer.exe
```

The `.spec` file is configured for proper resource bundling (styles, artwork cache, etc.).

## Project Structure

```
music-player/
├── src/
│   ├── backend/
│   │   ├── services/      # Business logic
│   │   │   ├── library.py      # Library scanning & queries
│   │   │   ├── playback.py     # VLC audio playback
│   │   │   ├── queue.py        # Playback queue management
│   │   │   ├── playlist.py     # Playlist CRUD
│   │   │   └── settings.py     # JSON settings persistence
│   │   ├── models/        # Data models (Song, Album, Artist, etc.)
│   │   ├── utils/         # Metadata, file scanning, database
│   │   └── exceptions.py  # Custom exceptions
│   ├── frontend/
│   │   ├── ui/            # Main views (Songs, Albums, Artists, etc.)
│   │   ├── components/    # Reusable UI components
│   │   └── resources/     # QSS stylesheet, icons
│   └── main.py            # Application entry point
├── tests/
│   ├── backend/           # Backend unit/integration tests
│   └── frontend/          # Frontend component tests
├── docs/                  # Additional documentation
├── requirements.txt       # Runtime dependencies
├── pyproject.toml         # Project metadata (Poetry)
├── setup.py               # Setuptools configuration
├── MusicPlayer.spec       # PyInstaller spec
├── LICENSE                # MIT License
├── README.md              # This file
├── CONTRIBUTING.md        # Contribution guidelines
├── CHANGELOG.md           # Version history
├── .gitignore             # Git ignore rules
└── AGENTS.md              # Architecture documentation
```

## Architecture Overview

The project follows a clean **backend/frontend separation** defined in `AGENTS.md`:

### Backend Services (Pure Python, No Qt)

| Service | Responsibility |
|---------|----------------|
| `LibraryService` | File scanning, metadata extraction, SQLite/FTS5 queries |
| `PlaybackService` | VLC wrapper, position polling, callbacks |
| `QueueService` | In-memory queue, repeat/shuffle logic |
| `PlaylistService` | Playlist CRUD, song associations |
| `SettingsService` | JSON-serialized SQLite settings |

### Frontend (PySide6/Qt6)

- **MainWindow**: Central coordinator, sidebar navigation, now-playing bar
- **Views**: SongsView, AlbumsView, ArtistsView, GenresView, PlaylistPanel, QueuePanel, SearchView
- **Components**: Sidebar, NowPlayingBar, ParticleWidget (background effects)
- **Styling**: Dark burgundy glassmorphism via QSS (`style.qss`)

### Data Flow

```
User Action (UI) → Service Method → Database/VLC → Callback → UI Update (via Qt signals)
```

Backend services emit events via callbacks. Frontend registers callbacks on startup and updates UI reactively. No direct frontend→backend calls for playback state — use callbacks only.

## Configuration

Settings are stored in SQLite (`settings` table) and include:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `library_paths` | `List[str]` | `[]` | Directories to scan for music |
| `volume` | `float` | `0.7` | Master volume (0.0-1.0) |
| `shuffle` | `bool` | `false` | Shuffle playback order |
| `repeat_mode` | `str` | `"off"` | `"off"`, `"one"`, `"all"` |
| `theme` | `str` | `"dark"` | `"dark"`, `"light"`, `"system"` |
| `minimize_to_tray` | `bool` | `true` | Minimize to system tray |
| `start_minimized` | `bool` | `false` | Start minimized to tray |
| `auto_scan_on_startup` | `bool` | `true` | Auto-scan library on launch |

## Database Schema

The app uses SQLite with FTS5 virtual tables for search:

- **songs** - Core track metadata + FTS5 (`songs_fts`)
- **albums** - Album aggregates + FTS5 (`albums_fts`)
- **artists** - Artist aggregates + FTS5 (`artists_fts`)
- **genres** - Genre list with song counts
- **playlists** - User playlists
- **playlist_songs** - Junction table (ordered)
- **queue** - Playback queue (ordered)
- **settings** - Key-value JSON settings

Triggers keep FTS5 tables in sync automatically.

## Development

### Code Quality Tools

```bash
# Format code
black src/ tests/

# Lint
ruff src/ tests/

# Type check
mypy src/

# Run all checks
black src/ tests/ && ruff src/ tests/ && mypy src/
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# Backend only
pytest tests/backend/ -v

# Frontend only
pytest tests/frontend/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Adding New Audio Formats

1. Add extraction logic in `src/backend/utils/metadata.py`
2. Register in `extract_metadata()` dispatcher
3. Add format to `get_audio_files()` in `src/backend/utils/files.py`
4. Add tests in `tests/backend/`

## Dependencies

### Runtime (requirements.txt)

| Package | Purpose |
|---------|---------|
| `PySide6>=6.6.0` | Qt6 GUI framework |
| `mutagen>=1.47.0` | Audio metadata extraction |
| `python-vlc>=3.0.20` | VLC Python bindings (audio playback) |
| `watchdog>=3.0.0` | File system watching (auto-scan) |
| `Pillow>=10.0.0` | Image processing (artwork) |

### Development

| Package | Purpose |
|---------|---------|
| `pytest>=7.4.0` | Testing framework |
| `pytest-qt>=4.2.0` | Qt test utilities |
| `pytest-cov>=4.1.0` | Coverage reporting |
| `black>=23.0.0` | Code formatting |
| `ruff>=0.1.0` | Fast linting |
| `mypy>=1.5.0` | Static type checking |
| `pyinstaller>=6.0.0` | Windows executable packaging |

## Troubleshooting

### No Audio / VLC Errors

1. Ensure **VLC Media Player** is installed (not just python-vlc)
2. On Windows: Install 64-bit VLC matching your Python architecture
3. On Linux: `sudo apt install vlc libvlc-dev` or equivalent
4. On macOS: `brew install vlc`

### Library Scan Finds No Files

- Check that your music folders contain supported formats
- Verify folder permissions
- Check console logs for scan errors

### UI Doesn't Load / Style Issues

- Ensure `style.qss` is bundled correctly (PyInstaller spec handles this)
- In development, run from project root so relative paths work

### Database Errors

- Delete `~/.local/share/MusicPlayer/songs.db` (or `%APPDATA%\MusicPlayer\songs.db` on Windows) to reset
- Run `python -c "from src.backend.utils.database import reset_database; reset_database()"`

## Roadmap

- [ ] Global hotkeys (media keys)
- [ ] Last.fm / ListenBrainz scrobbling
- [ ] Lyrics display (synced + unsynced)
- [ ] Equalizer & audio effects
- [ ] Smart playlists (recent, top rated, etc.)
- [ ] Mini-player mode
- [ ] Import/export playlists (M3U, PLS)
- [ ] MusicBrainz integration for metadata enrichment
- [ ] Remote control via HTTP API
- [ ] Mobile companion app

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Reporting bugs
- Suggesting features
- Code style & architecture
- Pull request process

## License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [PySide6](https://wiki.qt.io/Qt_for_Python) - Qt6 Python bindings
- [python-vlc](https://github.com/oaubert/python-vlc) - VLC Python bindings
- [mutagen](https://github.com/quodlibet/mutagen) - Audio metadata library
- [watchdog](https://github.com/gorakhargosh/watchdog) - File system events
- [Pillow](https://python-pillow.org/) - Image processing

## Support

- **Issues**: [GitHub Issues](https://github.com/deeptech760-stack/music-player/issues)
- **Discussions**: [GitHub Discussions](https://github.com/deeptech760-stack/music-player/discussions)
- **Security**: Report vulnerabilities privately via GitHub Security Advisories

---

**Made with ❤️ by [deeptech760-stack](https://github.com/deeptech760-stack)**