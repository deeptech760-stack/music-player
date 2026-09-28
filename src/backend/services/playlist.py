"""PlaylistService implementation for playlist management."""
from __future__ import annotations
import threading
from datetime import datetime
from typing import Optional, List, Callable

from src.backend.services.interfaces import PlaylistService
from src.backend.models import Song, Playlist
from src.backend.services.database import get_connection


def _parse_datetime(value) -> datetime:
    """Parse datetime from various SQLite formats."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    return datetime.now()


class PlaylistServiceImpl(PlaylistService):
    """Implementation of PlaylistService for playlist management."""

    def __init__(self) -> None:
        """Initialize playlist service."""
        self.db = get_connection()

    def get_all_playlists(self) -> List[Playlist]:
        """Get all playlists."""
        con = get_connection()
        con.execute("PRAGMA foreign_keys = ON")
        cur = con.cursor()
        cur.execute("""
            SELECT 
                p.id,
                p.name,
                p.created_at,
                p.updated_at,
                COUNT(ps.song_id) as song_count,
                COALESCE(SUM(s.duration), 0) as total_duration
            FROM playlists p
            LEFT JOIN playlist_songs ps ON p.id = ps.playlist_id
            LEFT JOIN songs s ON ps.song_id = s.id
            GROUP BY p.id
            ORDER BY p.name
        """)
        rows = cur.fetchall()
        playlists = [
            Playlist(
                id=row["id"],
                name=row["name"].decode() if isinstance(row["name"], bytes) else row["name"],
                song_count=row["song_count"] or 0,
                total_duration=float(row["total_duration"]) or 0.0,
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]
        return playlists

    def get_playlist(self, playlist_id: int) -> Optional[Playlist]:
        """Get a playlist by ID."""
        con = get_connection()
        con.execute("PRAGMA foreign_keys = ON")
        cur = con.cursor()
        query = """
            SELECT p.id, p.name, p.created_at, p.updated_at
            FROM playlists p
            WHERE p.id = ?
        """
        cur.execute(query, (playlist_id,))
        row = cur.fetchone()
        if not row:
            return None
        return Playlist(
            id=row["id"],
            name=row["name"].decode() if isinstance(row["name"], bytes) else row["name"],
            song_count=0,
            total_duration=0.0,
            created_at=_parse_datetime(row["created_at"]),
            updated_at=_parse_datetime(row["updated_at"]),
        )

    def create_playlist(self, name: str) -> Playlist:
        """Create a new playlist."""
        con = get_connection()
        con.execute("PRAGMA foreign_keys = ON")
        cur = con.cursor()
        try:
            cur.execute("INSERT INTO playlists (name) VALUES (?)", (name,))
            playlist_id = cur.lastrowid
            created_at = datetime.now()
            con.commit()
            return Playlist(
                id=playlist_id,
                name=name,
                song_count=0,
                total_duration=0.0,
                created_at=created_at,
                updated_at=created_at,
            )
        except Exception as e:
            con.rollback()
            # If duplicate name, try with suffix
            if "UNIQUE constraint failed" in str(e):
                base_name = name
                counter = 2
                while True:
                    new_name = f"{base_name} ({counter})"
                    try:
                        cur.execute("INSERT INTO playlists (name) VALUES (?)", (new_name,))
                        playlist_id = cur.lastrowid
                        created_at = datetime.now()
                        con.commit()
                        return Playlist(
                            id=playlist_id,
                            name=new_name,
                            song_count=0,
                            total_duration=0.0,
                            created_at=created_at,
                            updated_at=created_at,
                        )
                    except Exception:
                        counter += 1
                        continue
            raise PlaylistServiceError(f"Failed to create playlist: {e}")

    def delete_playlist(self, playlist_id: int) -> None:
        """Delete a playlist."""
        con = get_connection()
        con.execute("PRAGMA foreign_keys = ON")
        cur = con.cursor()
        try:
            cur.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
            con.commit()
        except Exception as e:
            con.rollback()
            raise PlaylistServiceError(f"Failed to delete playlist: {e}")

    def rename_playlist(self, playlist_id: int, name: str) -> None:
        """Rename a playlist."""
        con = get_connection()
        con.execute("PRAGMA foreign_keys = ON")
        cur = con.cursor()
        try:
            cur.execute("UPDATE playlists SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                       (name, playlist_id))
            con.commit()
        except Exception as e:
            con.rollback()
            raise PlaylistServiceError(f"Failed to rename playlist: {e}")

    def get_playlist_songs(self, playlist_id: int) -> List[Song]:
        """Get songs in a playlist."""
        con = get_connection()
        cur = con.cursor()
        cur.execute("""
            SELECT s.*
            FROM songs s
            INNER JOIN playlist_songs ps ON s.id = ps.song_id
            WHERE ps.playlist_id = ?
            ORDER BY ps.order_index
        """, (playlist_id,))
        rows = cur.fetchall()
        return [
            Song(
                id=row["id"],
                path=row["path"],
                title=row["title"],
                artist=row["artist"],
                album=row["album"],
                album_artist=row["album_artist"],
                genre=row["genre"],
                year=row["year"],
                track_number=row["track_number"],
                disc_number=row["disc_number"],
                duration=row["duration"],
                bitrate=row["bitrate"],
                sample_rate=row["sample_rate"],
                channels=row["channels"],
                file_size=row["file_size"],
                date_added=_parse_datetime(row["date_added"]),
                artwork_path=row["artwork_path"],
            )
            for row in rows
        ]

    def add_to_playlist(self, playlist_id: int, song: Song) -> None:
        """Add song to playlist."""
        con = get_connection()
        con.execute("PRAGMA foreign_keys = ON")
        cur = con.cursor()
        cur.execute("""
            INSERT INTO playlist_songs (playlist_id, song_id, order_index)
            VALUES (?, ?, COALESCE((SELECT MAX(order_index) FROM playlist_songs WHERE playlist_id = ?)+1, 0))
        """, (playlist_id, song.id, playlist_id))
        con.commit()

    def remove_from_playlist(self, playlist_id: int, song_id: int) -> None:
        """Remove song from playlist."""
        con = get_connection()
        con.execute("PRAGMA foreign_keys = ON")
        cur = con.cursor()
        cur.execute("DELETE FROM playlist_songs WHERE playlist_id = ? AND song_id = ?",
                   (playlist_id, song_id))
        con.commit()

    def reorder_playlist(self, playlist_id: int, from_index: int, to_index: int) -> None:
        """Reorder songs in playlist."""
        con = get_connection()
        con.execute("PRAGMA foreign_keys = ON")
        cur = con.cursor()
        try:
            # Get songs to reorder
            cur.execute("""
                SELECT song_id, order_index
                FROM playlist_songs
                WHERE playlist_id = ?
                ORDER BY order_index
                LIMIT ?
            """, (playlist_id, from_index + 1))
            songs_to_move = cur.fetchall()

            # Delete and reinsert with new order indices
            if to_index < from_index:
                from_offset = 1
            
            cur.execute(f"""
                DELETE FROM playlist_songs
                WHERE playlist_id = ? AND (SELECT ROW_NUMBER() OVER (ORDER BY order_index) ) <= {from_index + 1}
            """, (playlist_id,))

            # Reinsert songs with new indices
            new_index = to_index
            new_position = 0
            for song_id, old_order in songs_to_move:
                cur.execute("""
                    INSERT INTO playlist_songs (playlist_id, song_id, order_index)
                    VALUES (?, ?, ?)
                """, (playlist_id, song_id, new_index))
                self.db.commit()
                new_index += 1

            # Update remaining songs indices
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise PlaylistServiceError(f"Failed to reorder playlist: {e}")

    def update_playlist_data(self, playlist_id: int) -> None:
        """Update playlist song_count and total_duration."""
        con = get_connection()
        cur = con.cursor()
        cur.execute("""
            UPDATE playlists
            SET 
                song_count = (SELECT COUNT(*) FROM playlist_songs WHERE playlist_id = ?),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (playlist_id, playlist_id))
        con.commit()


class PlaylistServiceError(Exception):
    """Exception raised by PlaylistService."""
    pass


__all__ = ['PlaylistService', 'PlaylistServiceImpl', 'PlaylistServiceError']
