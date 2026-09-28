# Music Player - Agent Instructions

## Project Overview
Windows desktop music player built with Python (PySide6) and SQLite.

## Directory Structure
```
music-player/
├── src/
│   ├── backend/
│   │   ├── services/     # Business logic services
│   │   ├── models/       # Data models and database schema
│   │   └── utils/        # Utility functions
│   └── frontend/
│       ├── ui/           # Main window and views
│       ├── components/   # Reusable UI components
│       └── resources/    # Styles, icons, assets
├── tests/
│   ├── backend/
│   └── frontend/
├── docs/
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Build / Run / Test / Package Commands

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Application
```bash
python -m src.main
```

### Run Backend Tests
```bash
pytest tests/backend -v
```

### Run Frontend Tests
```bash
pytest tests/frontend -v
```

### Run All Tests
```bash
pytest tests/ -v
```

### Package as Windows .exe (PyInstaller)
```bash
pyinstaller --name "MusicPlayer" \
  --onefile \
  --windowed \
  --icon=src/frontend/resources/icon.ico \
  --add-data "src/frontend/resources;frontend/resources" \
  --add-data "src/backend;backend" \
  src/main.py
```

### Development Commands
```bash
# Format code
black src/ tests/

# Type check
mypy src/

# Lint
ruff src/ tests/
```

## Technology Stack
- **Language**: Python 3.11+
- **GUI Framework**: PySide6 (Qt6)
- **Database**: SQLite (via sqlite3 stdlib)
- **Audio**: python-vlc or pygame for playback
- **Metadata**: mutagen
- **Testing**: pytest + pytest-qt
- **Packaging**: PyInstaller

## Ownership Boundaries

### Coder (Backend) Owns
- `src/backend/` - All backend implementation
- Database schema and migrations
- Library scanning and file watching
- Metadata extraction (mutagen)
- Audio playback service (vlc/pygame wrapper)
- Queue and playlist logic
- Search engine (SQLite FTS5)
- Settings persistence
- Service interfaces (abstract base classes)
- Backend unit/integration tests

### Frontend Owns
- `src/frontend/` - All frontend implementation
- Main window and layout
- Sidebar navigation
- Library views (songs, albums, artists, genres)
- Now-playing bar
- Playback controls
- Queue panel
- Playlist panel
- Search UI
- Settings dialog
- Artwork display and caching
- Dark burgundy glassmorphism theme (QSS)
- Frontend component tests

### Lead Owns
- `src/main.py` - Application entry point (wiring only)
- `AGENTS.md` - This file
- `requirements.txt` / `pyproject.toml`
- Architecture documentation
- Interface contracts
- PyInstaller spec/build
- Integration verification

## Interface Contracts

The backend exposes these service interfaces that the frontend consumes:

### `LibraryService`
- `scan_library(paths: List[str]) -> ScanResult`
- `get_all_songs() -> List[Song]`
- `get_all_albums() -> List[Album]`
- `get_all_artists() -> List[Artist]`
- `get_all_genres() -> List[Genre]`
- `get_songs_by_album(album_id: int) -> List[Song]`
- `get_songs_by_artist(artist_id: int) -> List[Song]`
- `get_songs_by_genre(genre_id: int) -> List[Song]`
- `search(query: str) -> SearchResult`

### `PlaybackService`
- `play(song: Song) -> None`
- `pause() -> None`
- `resume() -> None`
- `stop() -> None`
- `seek(position: float) -> None`  # 0.0-1.0
- `set_volume(volume: float) -> None`  # 0.0-1.0
- `get_position() -> float`
- `get_duration() -> float`
- `get_state() -> PlaybackState`
- `on_position_changed(callback) -> None`
- `on_state_changed(callback) -> None`
- `on_track_finished(callback) -> None`

### `QueueService`
- `get_queue() -> List[QueueItem]`
- `add_to_queue(song: Song, position: Optional[int] = None) -> None`
- `remove_from_queue(index: int) -> None`
- `move_in_queue(from_index: int, to_index: int) -> None`
- `clear_queue() -> None`
- `set_current_index(index: int) -> None`
- `get_current_index() -> int`
- `on_queue_changed(callback) -> None`

### `PlaylistService`
- `create_playlist(name: str) -> Playlist`
- `delete_playlist(playlist_id: int) -> None`
- `rename_playlist(playlist_id: int, name: str) -> None`
- `get_all_playlists() -> List[Playlist]`
- `get_playlist(playlist_id: int) -> Playlist`
- `add_to_playlist(playlist_id: int, song: Song) -> None`
- `remove_from_playlist(playlist_id: int, song_id: int) -> None`
- `reorder_playlist(playlist_id: int, from_index: int, to_index: int) -> None`

### `SettingsService`
- `get(key: str) -> Any`
- `set(key: str, value: Any) -> None`
- `get_all() -> Dict[str, Any]`
- `reset_to_defaults() -> None`

## Data Models

### Song
```python
@dataclass
class Song:
    id: int
    path: str
    title: str
    artist: str
    album: str
    album_artist: str
    genre: str
    year: int
    track_number: int
    disc_number: int
    duration: float  # seconds
    bitrate: int
    sample_rate: int
    channels: int
    file_size: int
    date_added: datetime
    artwork_path: Optional[str] = None
```

### Album
```python
@dataclass
class Album:
    id: int
    name: str
    artist: str
    year: int
    genre: str
    song_count: int
    total_duration: float
    artwork_path: Optional[str] = None
```

### Artist
```python
@dataclass
class Artist:
    id: int
    name: str
    album_count: int
    song_count: int
```

### Genre
```python
@dataclass
class Genre:
    id: int
    name: str
    song_count: int
```

### Playlist
```python
@dataclass
class Playlist:
    id: int
    name: str
    song_count: int
    total_duration: float
    created_at: datetime
    updated_at: datetime
```

### QueueItem
```python
@dataclass
class QueueItem:
    index: int
    song: Song
    added_at: datetime
```

### PlaybackState
```python
class PlaybackState(Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    BUFFERING = "buffering"
    ERROR = "error"
```

### ScanResult
```python
@dataclass
class ScanResult:
    files_scanned: int
    files_added: int
    files_updated: int
    files_removed: int
    errors: List[str]
    duration_seconds: float
```

### SearchResult
```python
@dataclass
class SearchResult:
    songs: List[Song]
    albums: List[Album]
    artists: List[Artist]
    playlists: List[Playlist]
```

## Settings Keys
- `library_paths` - List[str]: Directories to scan
- `volume` - float: 0.0-1.0
- `shuffle` - bool
- `repeat_mode` - str: "off", "one", "all"
- `theme` - str: "dark", "light", "system"
- `minimize_to_tray` - bool
- `start_minimized` - bool
- `auto_scan_on_startup` - bool

## Communication Pattern
Backend services emit events via callbacks. Frontend registers callbacks on startup and updates UI reactively. No direct frontend→backend calls for playback state — use callbacks only.

## Error Handling
- Backend raises `BackendError` subclasses for recoverable errors
- Frontend catches and displays user-friendly messages
- Logging via Python `logging` module (backend logs to file, frontend to console)

## Testing Requirements
- Backend: Unit tests for all services, integration tests for database + playback
- Frontend: Component tests for key widgets, integration tests for main flows
- Coverage target: >80% for backend, >60% for frontend