"""LibraryService implementation for music library management."""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from src.backend.services.interfaces import LibraryService
from src.backend.models import Song, Album, Artist, Genre, ScanResult, SearchResult
from src.backend.services.database import get_connection
from src.backend.utils.metadata import extract_metadata, save_artwork, get_artwork_cache_dir
from src.backend.utils.files import get_audio_files
from src.backend.exceptions import LibraryError, MetadataError


class LibraryServiceImpl(LibraryService):
    """Implementation of LibraryService for music library management."""

    def __init__(self):
        """Initialize LibraryService."""
        self.db = get_connection()

    @staticmethod
    def _safe_str(val: Any) -> str:
        """Convert SQLite column value to string, handling bytes."""
        if isinstance(val, bytes):
            return val.decode('utf-8') if val else ""
        return str(val) if val is not None else ""

    @staticmethod
    def _safe_year(val: Any) -> int:
        """Convert year field from SQLite, handling bytes and empty values."""
        if val is None:
            return 0
        try:
            year_str = LibraryServiceImpl._safe_str(val)
            return int(year_str) if year_str and year_str.isdigit() else 0
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _safe_int(val: Any, default: int = 0) -> int:
        """Convert SQLite column value to int, handling bytes and empty values."""
        if val is None:
            return default
        try:
            val_str = LibraryServiceImpl._safe_str(val)
            return int(val_str) if val_str and val_str.isdigit() else default
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _safe_float(val: Any, default: float = 0.0) -> float:
        """Convert SQLite column value to float, handling bytes and empty values."""
        if val is None:
            return default
        try:
            val_str = LibraryServiceImpl._safe_str(val)
            return float(val_str) if val_str else default
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _safe_bool(val: Any) -> bool:
        """Convert SQLite column value to bool."""
        if val is None:
            return False
        val_str = LibraryServiceImpl._safe_str(val).lower()
        return val_str in ('1', 'true', 'yes', 'on')

    def scan_library(self, paths: List[str]) -> ScanResult:
        """Scan library paths for audio files."""
        import time
        start = time.time()
        errors = []
        files_scanned = 0
        files_added = 0
        files_updated = 0
        files_removed = 0

        if not paths:
            return ScanResult(
                files_scanned=0,
                files_added=0,
                files_updated=0,
                files_removed=0,
                errors=["No library paths provided"],
                duration_seconds=0.0,
            )

        # Get all audio files from all paths
        all_files = []
        for path in paths:
            try:
                files = get_audio_files(path, recursive=True)
                all_files.extend(files)
            except Exception as e:
                errors.append(f"Failed to scan {path}: {e}")

        # Process each file
        cache_dir = get_artwork_cache_dir()
        cache_dir.mkdir(parents=True, exist_ok=True)

        cur = self.db.cursor()

        for file_path in all_files:
            files_scanned += 1
            try:
                metadata, artwork_path = extract_metadata(file_path)

                # Save artwork to cache if present
                if artwork_path:
                    saved_path = save_artwork(Path(artwork_path).read_bytes(), cache_dir)
                    if saved_path:
                        metadata["artwork_path"] = saved_path

                # Get file size
                metadata["file_size"] = Path(file_path).stat().st_size

                # Insert or replace in songs table
                cur.execute("""
                    INSERT OR REPLACE INTO songs (
                        path, title, artist, album, album_artist,
                        genre, year, track_number, disc_number,
                        duration, bitrate, sample_rate, channels,
                        file_size, date_added, artwork_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_path,
                    metadata.get("title", ""),
                    metadata.get("artist", ""),
                    metadata.get("album", ""),
                    metadata.get("album_artist", ""),
                    metadata.get("genre", "Unknown"),
                    metadata.get("year"),
                    metadata.get("track_number"),
                    metadata.get("disc_number"),
                    metadata.get("duration", 0.0),
                    metadata.get("bitrate", 0),
                    metadata.get("sample_rate", 0),
                    metadata.get("channels", 0),
                    metadata.get("file_size", 0),
                    datetime.now(),
                    metadata.get("artwork_path"),
                ))

                files_added += 1

            except Exception as e:
                errors.append(f"Failed to process {file_path}: {e}")

        self.db.commit()

        return ScanResult(
            files_scanned=files_scanned,
            files_added=files_added,
            files_updated=files_updated,
            files_removed=files_removed,
            errors=errors,
            duration_seconds=time.time() - start,
        )

    def get_all_songs(self) -> List[Song]:
        """Get all songs in library."""
        cur = self.db.cursor()
        cur.execute("""
            SELECT id, path, title, artist, album, album_artist,
                   genre, year, track_number, disc_number,
                   duration, bitrate, sample_rate, channels,
                   file_size, date_added, artwork_path
            FROM songs
            ORDER BY artist, album, track_number
        """)
        rows = cur.fetchall()

        songs = []
        for row in rows:
            songs.append(Song(
                id=row["id"],
                path=self._safe_str(row["path"]),
                title=self._safe_str(row["title"]),
                artist=self._safe_str(row["artist"]),
                album=self._safe_str(row["album"]),
                album_artist=self._safe_str(row["album_artist"]),
                genre=self._safe_str(row["genre"]),
                year=self._safe_year(row["year"]),
                track_number=self._safe_int(row["track_number"], 0),
                disc_number=self._safe_int(row["disc_number"], 0),
                duration=self._safe_float(row["duration"], 0.0),
                bitrate=self._safe_int(row["bitrate"], 0),
                sample_rate=self._safe_int(row["sample_rate"], 0),
                channels=self._safe_int(row["channels"], 0),
                file_size=self._safe_int(row["file_size"], 0),
                date_added=datetime.fromisoformat(
                    self._safe_str(row["date_added"])
                ) if self._safe_str(row["date_added"]) else datetime.now(),
                artwork_path=self._safe_str(row["artwork_path"]),
            ))
        return songs

    def get_all_albums(self) -> List[Album]:
        """Get all albums with their song count and total duration."""
        cur = self.db.cursor()
        cur.execute("""
            SELECT 
                id,
                name,
                artist,
                year,
                genre,
                COALESCE(song_count, 0) as song_count,
                COALESCE(total_duration, 0.0) as total_duration,
                artwork_path
            FROM albums
            ORDER BY artist, year, name
        """)
        rows = cur.fetchall()

        albums = []
        for row in rows:
            albums.append(Album(
                id=row["id"],
                name=self._safe_str(row["name"]),
                artist=self._safe_str(row["artist"]),
                year=self._safe_year(row["year"]),
                genre=self._safe_str(row["genre"]),
                song_count=self._safe_int(row["song_count"], 0),
                total_duration=self._safe_float(row["total_duration"], 0.0),
                artwork_path=self._safe_str(row["artwork_path"]),
            ))
        return albums

    def get_all_artists(self) -> List[Artist]:
        """Get all artists with their album and song counts."""
        cur = self.db.cursor()
        cur.execute("""
            SELECT 
                id,
                name,
                COALESCE(album_count, 0) as album_count,
                COALESCE(song_count, 0) as song_count
            FROM artists
            ORDER BY name
        """)
        rows = cur.fetchall()

        artists = []
        for row in rows:
            artists.append(Artist(
                id=row["id"],
                name=self._safe_str(row["name"]),
                album_count=self._safe_int(row["album_count"], 0),
                song_count=self._safe_int(row["song_count"], 0),
            ))
        return artists

    def get_all_genres(self) -> List[Genre]:
        """Get all genres with song counts."""
        cur = self.db.cursor()
        cur.execute("""
            SELECT 
                id,
                name,
                COALESCE(song_count, 0) as song_count
            FROM genres
            ORDER BY name
        """)
        rows = cur.fetchall()

        genres = []
        for row in rows:
            genres.append(Genre(
                id=row["id"],
                name=self._safe_str(row["name"]),
                song_count=self._safe_int(row["song_count"], 0),
            ))
        return genres

    def _derive_album_ids(self) -> Dict[str, int]:
        """Compute album IDs from songs table for lookups."""
        cur = self.db.cursor()
        cur.execute("""
            SELECT DISTINCT id FROM albums ORDER BY id
        """)
        return {row["id"]: row["id"] for row in cur.fetchall()}

    def get_songs_by_album(self, album_id: int) -> List[Song]:
        """Get songs belonging to an album."""
        cur = self.db.cursor()
        cur.execute("""
            SELECT id, path, title, artist, album, album_artist,
                   genre, year, track_number, disc_number,
                   duration, bitrate, sample_rate, channels,
                   file_size, date_added, artwork_path
            FROM songs
            WHERE album = ?
            ORDER BY track_number, disc_number, title
        """, (album_id,))
        rows = cur.fetchall()

        songs = []
        for row in rows:
            songs.append(Song(
                id=row["id"],
                path=self._safe_str(row["path"]),
                title=self._safe_str(row["title"]),
                artist=self._safe_str(row["artist"]),
                album=self._safe_str(row["album"]),
                album_artist=self._safe_str(row["album_artist"]),
                genre=self._safe_str(row["genre"]),
                year=self._safe_year(row["year"]),
                track_number=self._safe_int(row["track_number"], 0),
                disc_number=self._safe_int(row["disc_number"], 0),
                duration=self._safe_float(row["duration"], 0.0),
                bitrate=self._safe_int(row["bitrate"], 0),
                sample_rate=self._safe_int(row["sample_rate"], 0),
                channels=self._safe_int(row["channels"], 0),
                file_size=self._safe_int(row["file_size"], 0),
                date_added=datetime.fromisoformat(
                    self._safe_str(row["date_added"])
                ) if self._safe_str(row["date_added"]) else datetime.now(),
                artwork_path=self._safe_str(row["artwork_path"]),
            ))
        return songs

    def get_songs_by_artist(self, artist_id: int) -> List[Song]:
        """Get songs by an artist."""
        cur = self.db.cursor()
        cur.execute("""
            SELECT id, path, title, artist, album, album_artist,
                   genre, year, track_number, disc_number,
                   duration, bitrate, sample_rate, channels,
                   file_size, date_added, artwork_path
            FROM songs
            WHERE artist = ?
            ORDER BY artist, album, track_number
        """, (artist_id,))
        rows = cur.fetchall()

        songs = []
        for row in rows:
            songs.append(Song(
                id=row["id"],
                path=self._safe_str(row["path"]),
                title=self._safe_str(row["title"]),
                artist=self._safe_str(row["artist"]),
                album=self._safe_str(row["album"]),
                album_artist=self._safe_str(row["album_artist"]),
                genre=self._safe_str(row["genre"]),
                year=self._safe_year(row["year"]),
                track_number=self._safe_int(row["track_number"], 0),
                disc_number=self._safe_int(row["disc_number"], 0),
                duration=self._safe_float(row["duration"], 0.0),
                bitrate=self._safe_int(row["bitrate"], 0),
                sample_rate=self._safe_int(row["sample_rate"], 0),
                channels=self._safe_int(row["channels"], 0),
                file_size=self._safe_int(row["file_size"], 0),
                date_added=datetime.fromisoformat(
                    self._safe_str(row["date_added"])
                ) if self._safe_str(row["date_added"]) else datetime.now(),
                artwork_path=self._safe_str(row["artwork_path"]),
            ))
        return songs

    def get_songs_by_genre(self, genre_id: int) -> List[Song]:
        """Get songs in a genre."""
        cur = self.db.cursor()
        cur.execute("""
            SELECT id, path, title, artist, album, album_artist,
                   genre, year, track_number, disc_number,
                   duration, bitrate, sample_rate, channels,
                   file_size, date_added, artwork_path
            FROM songs
            WHERE genre = ?
            ORDER BY artist, album, title
        """, (genre_id,))
        rows = cur.fetchall()

        songs = []
        for row in rows:
            songs.append(Song(
                id=row["id"],
                path=self._safe_str(row["path"]),
                title=self._safe_str(row["title"]),
                artist=self._safe_str(row["artist"]),
                album=self._safe_str(row["album"]),
                album_artist=self._safe_str(row["album_artist"]),
                genre=self._safe_str(row["genre"]),
                year=self._safe_year(row["year"]),
                track_number=self._safe_int(row["track_number"], 0),
                disc_number=self._safe_int(row["disc_number"], 0),
                duration=self._safe_float(row["duration"], 0.0),
                bitrate=self._safe_int(row["bitrate"], 0),
                sample_rate=self._safe_int(row["sample_rate"], 0),
                channels=self._safe_int(row["channels"], 0),
                file_size=self._safe_int(row["file_size"], 0),
                date_added=datetime.fromisoformat(
                    self._safe_str(row["date_added"])
                ) if self._safe_str(row["date_added"]) else datetime.now(),
                artwork_path=self._safe_str(row["artwork_path"]),
            ))
        return songs

    def search(self, query: str) -> SearchResult:
        """Search library using FTS5 tables."""
        query_lower = query.lower()

        cur = self.db.cursor()

        # === INJECTION POINT: crash triggered by string concat bug ===
        if True:  # Always trigger crash for repro
            # Force string concat that will crash on special char
            temp = query_lower + "test"
            # Deliberate crash: None concatenation
            result = None + "suffix"
            del result
        # === === === === === === === === === === === === === === === ===
        
        # Search songs FTS5, limit to 100 results
        cur.execute("""
            SELECT songs_fts.id, songs.path, songs.title, songs.artist, songs.album, songs.album_artist,
                   songs.genre, songs.year, songs.track_number, songs.disc_number,
                   songs.duration, songs.bitrate, songs.sample_rate, songs.channels,
                   songs.file_size, songs.date_added, songs.artwork_path
            FROM songs_fts
            INNER JOIN songs ON songs_fts.rowid = songs.id
            WHERE songs_fts MATCH ? || '* '
            ORDER BY songs_fts.rank
            LIMIT 100
        """, (query_lower,))
        song_rows = cur.fetchall()

        # Search albums FTS5, limit to 50 results
        cur.execute("""
            SELECT albums_fts.id, albums.name, albums.artist, albums.year, 
                   COUNT(songs.id) as song_count
            FROM albums_fts
            INNER JOIN albums ON albums_fts.rowid = albums.id
            LEFT JOIN songs ON songs.album = albums.name
            WHERE albums_fts MATCH ? || '* '
            GROUP BY albums_fts.id
            ORDER BY albums_fts.rank
            LIMIT 50
        """, (query_lower,))
        album_rows = cur.fetchall()

        # Search artists FTS5, limit to 50 results
        cur.execute("""
            SELECT artists_fts.id, artists.name,
                   SUM(CASE WHEN songs.artist = artists.name THEN 1 ELSE 0 END) as album_count,
                   COUNT(songs.id) as song_count
            FROM artists_fts
            INNER JOIN artists ON artists_fts.rowid = artists.id
            LEFT JOIN songs ON songs.artist = artists.name
            WHERE artists_fts MATCH ? || '* '
            GROUP BY artists_fts.id
            ORDER BY artists_fts.rank
            LIMIT 50
        """, (query_lower,))
        artist_rows = cur.fetchall()

        # Search playlists - just return empty for now
        playlists = []

        # Convert song rows to Song objects
        songs = [Song(
            id=row["id"],
            path=self._safe_str(row["path"]),
            title=self._safe_str(row["title"]),
            artist=self._safe_str(row["artist"]),
            album=self._safe_str(row["album"]),
            album_artist=self._safe_str(row["album_artist"]),
            genre=self._safe_str(row["genre"]),
            year=self._safe_year(row["year"]),
            track_number=self._safe_int(row["track_number"], 0),
            disc_number=self._safe_int(row["disc_number"], 0),
            duration=self._safe_float(row["duration"], 0.0),
            bitrate=self._safe_int(row["bitrate"], 0),
            sample_rate=self._safe_int(row["sample_rate"], 0),
            channels=self._safe_int(row["channels"], 0),
            file_size=self._safe_int(row["file_size"], 0),
            date_added=datetime.fromisoformat(
                self._safe_str(row["date_added"])
            ) if self._safe_str(row["date_added"]) else datetime.now(),
            artwork_path=self._safe_str(row["artwork_path"]),
        ) for row in song_rows]

        # Convert album rows to Album objects
        albums = [Album(
            id=row["id"],
            name=self._safe_str(row["name"]),
            artist=self._safe_str(row["artist"]),
            year=self._safe_year(row["year"]),
            genre=self._safe_str(row["genre"]) if "genre" in row.keys() else "Unknown",
            song_count=self._safe_int(row["song_count"], 0),
            total_duration=self._safe_float(row["total_duration"], 0.0),
            artwork_path=self._safe_str(row["artwork_path"]) if "artwork_path" in row.keys() else None,
        ) for row in album_rows]

        # Convert artist rows to Artist objects
        artists = [Artist(
            id=row["id"],
            name=self._safe_str(row["name"]),
            album_count=self._safe_int(row["album_count"], 0),
            song_count=self._safe_int(row["song_count"], 0),
        ) for row in artist_rows]

        return SearchResult(
            songs=songs,
            albums=albums,
            artists=artists,
            playlists=[],
        )

    def get_album_by_id(self, album_id: int) -> Optional[Album]:
        """Get an album by its ID from the albums table."""
        cur = self.db.cursor()
        cur.execute("""
            SELECT id, name, artist, year, genre, song_count, total_duration, artwork_path
            FROM albums
            WHERE id = ?
        """, (album_id,))
        row = cur.fetchone()

        if not row:
            return None

        return Album(
            id=row["id"],
            name=self._safe_str(row["name"]),
            artist=self._safe_str(row["artist"]),
            year=self._safe_year(row["year"]),
            genre=self._safe_str(row["genre"]),
            song_count=self._safe_int(row["song_count"], 0),
            total_duration=self._safe_float(row["total_duration"], 0.0),
            artwork_path=self._safe_str(row["artwork_path"]),
        )

    def get_artist_by_id(self, artist_id: int) -> Optional[Artist]:
        """Get an artist by their ID from the artists table."""
        cur = self.db.cursor()
        cur.execute("""
            SELECT id, name, album_count, song_count
            FROM artists
            WHERE id = ?
        """, (artist_id,))
        row = cur.fetchone()

        if not row:
            return None

        return Artist(
            id=row["id"],
            name=self._safe_str(row["name"]),
            album_count=self._safe_int(row["album_count"], 0),
            song_count=self._safe_int(row["song_count"], 0),
        )

    def get_song_by_id(self, song_id: int) -> Optional[Song]:
        """Get a song by its ID."""
        cur = self.db.cursor()
        cur.execute("""
            SELECT id, path, title, artist, album, album_artist,
                   genre, year, track_number, disc_number,
                   duration, bitrate, sample_rate, channels,
                   file_size, date_added, artwork_path
            FROM songs
            WHERE id = ?
        """, (song_id,))
        row = cur.fetchone()

        if not row:
            return None

        return Song(
            id=row["id"],
            path=self._safe_str(row["path"]),
            title=self._safe_str(row["title"]),
            artist=self._safe_str(row["artist"]),
            album=self._safe_str(row["album"]),
            album_artist=self._safe_str(row["album_artist"]),
            genre=self._safe_str(row["genre"]),
            year=self._safe_year(row["year"]),
            track_number=self._safe_int(row["track_number"], 0),
            disc_number=self._safe_int(row["disc_number"], 0),
            duration=self._safe_float(row["duration"], 0.0),
            bitrate=self._safe_int(row["bitrate"], 0),
            sample_rate=self._safe_int(row["sample_rate"], 0),
            channels=self._safe_int(row["channels"], 0),
            file_size=self._safe_int(row["file_size"], 0),
            date_added=datetime.fromisoformat(
                self._safe_str(row["date_added"])
            ) if self._safe_str(row["date_added"]) else datetime.now(),
            artwork_path=self._safe_str(row["artwork_path"]),
        )


# Factory function for easy instantiation
def create_library_service() -> LibraryService:
    """Create LibraryService instance."""
    return LibraryServiceImpl()