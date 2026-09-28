"""Database connection and schema management."""
from __future__ import annotations
from pathlib import Path
from sqlite3 import Connection, connect, Row
from typing import Optional
import threading
import os


# Cache for database connection
_db_connection: Optional[Connection] = None
_db_lock = threading.Lock()
INITIALIZED = False


def get_db_path() -> Path:
    """Get the database file path from environment or default to APPDATA."""
    app_data = Path(os.environ.get("APPDATA", ""))
    if app_data and app_data.exists():
        db_path = app_data / "MusicPlayer" / "songs.db"
    else:
        # Fallback to temp
        db_path = Path(__file__).parent.parent.parent / "music-player" / "music-player CACHE" / "songs.db"
    return db_path


def get_connection() -> Connection:
    """Get or create database connection with lazy initialization."""
    global _db_connection, INITIALIZED
    
    if not INITIALIZED:
        with _db_lock:
            if not INITIALIZED:
                db_path = get_db_path()
                db_path.parent.mkdir(parents=True, exist_ok=True)
                _db_connection = connect(str(db_path), check_same_thread=False)
                _db_connection.row_factory = Row
                _db_connection.text_factory = lambda x: x or ""
                INITIALIZED = True
                _init_schema()
    
    return _db_connection


def _init_schema():
    """Initialize database schema with FTS5."""
    con = get_connection()
    cur = con.cursor()
    
    # Enable foreign keys
    cur.execute("PRAGMA foreign_keys = ON")
    
    # Create enums as separate tables for SQLite
    cur.execute("""
        CREATE TABLE IF NOT EXISTS playback_state (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            value TEXT NOT NULL
        )
    """)
    for i, (name, value) in enumerate([
        ("STOPPED", "stopped"),
        ("PLAYING", "playing"),
        ("PAUSED", "paused"),
        ("BUFFERING", "buffering"),
        ("ERROR", "error"),
    ], 1):
        cur.execute("INSERT OR IGNORE INTO playback_state VALUES (?, ?, ?)", (i, name, value))
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS repeat_mode (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            value TEXT NOT NULL
        )
    """)
    for i, (name, value) in enumerate([
        ("OFF", "off"),
        ("ONE", "one"),
        ("ALL", "all"),
    ], 1):
        cur.execute("INSERT OR IGNORE INTO repeat_mode VALUES (?, ?, ?)", (i, name, value))
    
    # Songs table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            artist TEXT NOT NULL,
            album TEXT NOT NULL,
            album_artist TEXT NOT NULL,
            genre TEXT NOT NULL DEFAULT 'Unknown',
            year INTEGER,
            track_number INTEGER,
            disc_number INTEGER,
            duration REAL NOT NULL,
            bitrate INTEGER,
            sample_rate INTEGER,
            channels INTEGER,
            file_size INTEGER,
            date_added DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            artwork_path TEXT
        )
    """)
    
    # Albums table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS albums (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            artist TEXT NOT NULL,
            year INTEGER,
            genre TEXT NOT NULL DEFAULT 'Unknown',
            song_count INTEGER NOT NULL DEFAULT 0,
            total_duration REAL NOT NULL DEFAULT 0,
            artwork_path TEXT
        )
    """)
    
    # Artists table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS artists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            album_count INTEGER NOT NULL DEFAULT 0,
            song_count INTEGER NOT NULL DEFAULT 0
        )
    """)
    
    # Genres table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS genres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            song_count INTEGER NOT NULL DEFAULT 0
        )
    """)
    
    # Playlists table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Playlist songs junction (ordered list)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS playlist_songs (
            playlist_id INTEGER NOT NULL,
            song_id INTEGER NOT NULL,
            order_index INTEGER NOT NULL,
            PRIMARY KEY (playlist_id, song_id),
            FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
            FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
        )
    """)
    
    # Queue table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id INTEGER NOT NULL,
            order_index INTEGER NOT NULL,
            added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
        )
    """)
    
    # Settings table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT NOT NULL PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    # Create FTS5 virtual tables for search
    cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS songs_fts
        USING fts5(
            title,
            artist,
            album,
            album_artist,
            content='songs',
            content_rowid='id'
        )
    """)
    
    # Create FTS5 for albums
    cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS albums_fts
        USING fts5(
            name,
            artist,
            content='albums',
            content_rowid='id'
        )
    """)
    
    # Create FTS5 for artists
    cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS artists_fts
        USING fts5(
            name,
            content='artists',
            content_rowid='id'
        )
    """)
    
    # Create triggers to keep FTS5 in sync
    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS songs_fts_insert
        AFTER INSERT ON songs
        BEGIN
            INSERT INTO songs_fts(rowid, title, artist, album, album_artist)
            VALUES(new.id, new.title, new.artist, new.album, new.album_artist);
        END
    """)
    
    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS songs_fts_delete
        AFTER DELETE ON songs
        BEGIN
            DELETE FROM songs_fts WHERE rowid = old.id;
        END
    """)
    
    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS songs_fts_update
        AFTER UPDATE ON songs
        BEGIN
            DELETE FROM songs_fts WHERE rowid = old.id;
            INSERT INTO songs_fts(rowid, title, artist, album, album_artist)
            VALUES(new.id, new.title, new.artist, new.album, new.album_artist);
        END
    """)
    
    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS albums_fts_insert
        AFTER INSERT ON albums
        BEGIN
            INSERT INTO albums_fts(rowid, name, artist)
            VALUES(new.id, new.name, new.artist);
        END
    """)
    
    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS albums_fts_delete
        AFTER DELETE ON albums
        BEGIN
            DELETE FROM albums_fts WHERE rowid = old.id;
        END
    """)
    
    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS artists_fts_insert
        AFTER INSERT ON artists
        BEGIN
            INSERT INTO artists_fts(rowid, name) VALUES(new.id, new.name);
        END
    """)
    
    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS artists_fts_delete
        AFTER DELETE ON artists
        BEGIN
            DELETE FROM artists_fts WHERE rowid = old.id;
        END
    """)
    
    con.commit()
    # DO NOT close connection - keep it alive


def init_database():
    """Initialize database schema."""
    with _db_lock:
        _init_schema()


def close_connection():
    """Close database connection."""
    global _db_connection, INITIALIZED
    if _db_connection:
        _db_connection.close()
        _db_connection = None
        INITIALIZED = False


def reset_database():
    """Reinitialize database schema (for testing)."""
    import shutil
    db_path = get_db_path()
    if db_path.exists():
        db_path.unlink()
    global _db_connection, INITIALIZED
    _db_connection = None
    INITIALIZED = False
    get_connection()  # Reinitialize


def ensure_database():
    """Ensure database exists and is initialized."""
    return get_connection()