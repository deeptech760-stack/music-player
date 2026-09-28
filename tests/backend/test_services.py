import pytest
import tempfile
import os
from pathlib import Path

# Test database
from src.backend.utils.database import get_connection as db_get_connection, reset_database, get_db_path, _db_connection, INITIALIZED, _db_lock, _init_schema
from src.backend.services.database import get_connection as svc_get_connection

# Test services
from src.backend.services.library import LibraryServiceImpl
from src.backend.services.queue import QueueServiceImpl
from src.backend.services.playlist import PlaylistServiceImpl
from src.backend.services.settings import SettingsServiceImpl
from src.backend.models import Song, Album, Artist, Genre, Playlist, QueueItem, DEFAULT_SETTINGS, RepeatMode


def _get_test_db_path():
    """Get temporary database path for tests."""
    import tempfile
    base_path = tempfile.gettempdir()
    db_name = "music-player-test-db"
    db_path = Path(base_path) / db_name
    return db_path


# Override database path for tests
_TEST_DB_PATH = None


@pytest.fixture(autouse=True)
def setup_test_db():
    """Set up a temporary database for testing."""
    global _TEST_DB_PATH
    _TEST_DB_PATH = _get_test_db_path()
    _TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Close any existing connection
    if _db_connection:
</think>

<tool_call>
<function=edit>
<parameter=path>
E:\playground\Projects\music-player\tests\backend\test_services.py


def test_database_connection():
    con = get_connection()
    assert con is not None
    row = con.execute("SELECT 1").fetchone()
    assert row[0] == 1


def test_database_schema():
    con = get_connection()
    tables = con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = [t[0] for t in tables]
    assert 'songs' in table_names
    assert 'playlists' in table_names
    assert 'queue' in table_names
    assert 'settings' in table_names


def test_settings_service():
    svc = SettingsServiceImpl()
    # Test defaults
    all_settings = svc.get_all()
    assert 'volume' in all_settings
    assert all_settings['volume'] == 0.7
    # Test get/set
    svc.set('test_key', 'test_value')
    assert svc.get('test_key') == 'test_value'
    # Test type coercion
    svc.set('test_bool', True)
    assert svc.get('test_bool') is True
    svc.set('test_int', 42)
    assert svc.get('test_int') == 42
    svc.set('test_list', [1,2,3])
    assert svc.get('test_list') == [1,2,3]
    # Test reset
    svc.reset_to_defaults()
    assert svc.get('volume') == 0.7


def test_queue_service():
    svc = QueueServiceImpl()
    # Create dummy songs
    con = get_connection()
    cur = con.cursor()
    cur.execute("INSERT INTO songs (path, title, artist, album, album_artist, genre, duration, bitrate, sample_rate, channels, file_size, date_added) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                ("/test1.mp3", "Song1", "Artist1", "Album1", "Artist1", "Rock", 180.0, 320, 44100, 2, 1000, "2024-01-01"))
    cur.execute("INSERT INTO songs (path, title, artist, album, album_artist, genre, duration, bitrate, sample_rate, channels, file_size, date_added) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                ("/test2.mp3", "Song2", "Artist2", "Album2", "Artist2", "Pop", 200.0, 320, 44100, 2, 1000, "2024-01-01"))
    con.commit()
    
    # Get songs
    lib = LibraryServiceImpl()
    songs = lib.get_all_songs()
    assert len(songs) >= 2
    
    # Add to queue
    svc.add_to_queue(songs[0])
    svc.add_to_queue(songs[1])
    queue = svc.get_queue()
    assert len(queue) == 2
    assert queue[0].song.title == "Song1"
    
    # Test current index
    assert svc.get_current_index() == 0
    svc.set_current_index(1)
    assert svc.get_current_index() == 1
    
    # Remove
    svc.remove_from_queue(0)
    queue = svc.get_queue()
    assert len(queue) == 1


def test_playlist_service():
    svc = PlaylistServiceImpl()
    # Create playlist
    pl = svc.create_playlist("Test Playlist")
    assert pl.name == "Test Playlist"
    assert pl.id > 0
    
    # Add songs (need songs in DB)
    con = get_connection()
    cur = con.cursor()
    cur.execute("INSERT INTO songs (path, title, artist, album, album_artist, genre, duration, bitrate, sample_rate, channels, file_size, date_added) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                ("/test3.mp3", "Song3", "Artist3", "Album3", "Artist3", "Jazz", 150.0, 320, 44100, 2, 1000, "2024-01-01"))
    con.commit()
    
    lib = LibraryServiceImpl()
    songs = lib.get_all_songs()
    if songs:
        svc.add_to_playlist(pl.id, songs[0])
        pl_songs = svc.get_playlist_songs(pl.id)
        assert len(pl_songs) == 1
    
    # Get all playlists
    playlists = svc.get_all_playlists()
    assert len(playlists) >= 1
    assert any(p.name == "Test Playlist" for p in playlists)


def test_library_service():
    svc = LibraryServiceImpl()
    # Scan empty path
    result = svc.scan_library([])
    assert result.files_scanned == 0
    assert "No library paths" in result.errors[0]
