"""Metadata extraction using mutagen."""
from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import hashlib

from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.oggflac import OggFLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.mp4 import MP4
from mutagen.id3 import ID3, APIC
from mutagen import File  # Generic handler for all formats including WAV/AIFF

import src.backend.exceptions as exc


def sanitize_string(value: str, max_length: int = 256) -> str:
    """Sanitize string for database storage."""
    if not value:
        return ""
    return str(value).strip().replace('\n', ' ').replace('\r', ' ')[:max_length]


def _get_default_metadata(path: str) -> Dict[str, Any]:
    """Create default metadata dict for a file."""
    path_obj = Path(path)
    metadata = {
        "path": path,
        "title": path_obj.stem,
        "artist": "",
        "album": "",
        "album_artist": "",
        "genre": "",
        "year": None,
        "track_number": None,
        "disc_number": None,
        "duration": 0.0,
        "bitrate": 0,
        "sample_rate": 0,
        "channels": 0,
        "file_size": 0,
        "artwork_path": None,
    }
    try:
        metadata["file_size"] = path_obj.stat().st_size
    except OSError:
        pass
    return metadata


def _extract_mp3(path: str) -> Tuple[Dict[str, Any], Optional[str]]:
    """Extract MP3 metadata."""
    path_obj = Path(path)
    metadata = _get_default_metadata(path)
    
    try:
        tags = MP3(path, ID3=ID3)
        
        # Read ID3 tags
        id3 = tags.tags if isinstance(tags.tags, ID3) else None
        
        # Title
        if id3 and id3.get("TIT2"):
            metadata["title"] = sanitize_string(id3["TIT2"].text[0])
        
        # Artist
        if id3 and id3.get("TPE1"):
            metadata["artist"] = sanitize_string(id3["TPE1"].text[0])
        
        # Album
        if id3 and id3.get("TALB"):
            metadata["album"] = sanitize_string(id3["TALB"].text[0])
        
        # Album artist
        if id3 and id3.get("TPE2"):
            metadata["album_artist"] = sanitize_string(id3["TPE2"].text[0])
        elif metadata["artist"]:
            metadata["album_artist"] = metadata["artist"]
        
        # Genre
        if id3 and id3.get("TCON"):
            genre_num = id3["TCON"].text[0]
            genre_map = {
                "0": "Blues", "1": "Classic Rock", "2": "Country", "3": "Dance",
                "4": "Disco", "5": "Funk", "6": "Grunge", "7": "Hip-Hop",
                "8": "Jazz", "9": "Metal", "10": "New Age", "11": "Opera",
                "12": "Pop", "13": "R&B", "14": "Reggae", "15": "Soul",
                "16": "Techno", "17": "Electronic", "18": "Experimental",
                "19": "Industrial", "20": "Alternative", "21": "Sketch",
                "22": "Musical", "23": "Roguewave", "24": "Soundtrack",
            }
            metadata["genre"] = genre_map.get(genre_num, genre_num)
        
        # Year
        if id3 and id3.get("TYER"):
            try:
                year = id3["TYER"].text[0]
                if year and year.isdigit():
                    metadata["year"] = int(year)
            except (IndexError, ValueError):
                pass
        
        # Track number
        if id3 and id3.get("TRCK"):
            try:
                track = id3["TRCK"].text[0].split("/")[0]
                if track.isdigit():
                    metadata["track_number"] = int(track)
            except (IndexError, ValueError):
                pass
        
        # Disc number
        if id3 and id3.get("TPOS"):
            try:
                disc = id3["TPOS"].text[0].split("/")[0]
                if disc.isdigit():
                    metadata["disc_number"] = int(disc)
            except (IndexError, ValueError):
                pass
        
        # Extract artwork
        if id3:
            pictures = id3.getall("APIC")
            for picture in pictures:
                if picture.type == 3:  # Front cover
                    metadata["artwork_path"] = picture.data
                    break
        
        # Bitrate
        if hasattr(tags.info, 'bitrate'):
            metadata["bitrate"] = tags.info.bitrate
        
        # Sample rate and channels
        if hasattr(tags.info, 'sample_rate'):
            metadata["sample_rate"] = tags.info.sample_rate or 44100
        if hasattr(tags.info, 'channels'):
            metadata["channels"] = tags.info.channels or 2
        
        # Duration
        if hasattr(tags.info, 'length'):
            metadata["duration"] = tags.info.length
        
        return metadata, metadata["artwork_path"]
        
    except Exception:
        return metadata, None


def _extract_flac_or_ogg(path: str) -> Tuple[Dict[str, Any], Optional[str]]:
    """Extract FLAC or OGG metadata."""
    path_obj = Path(path)
    metadata = _get_default_metadata(path)
    
    try:
        tags_obj = None
        # Try different mutagen tags
        for cls in (FLAC, OggFLAC, OggVorbis):
            try:
                tags_obj = cls(path)
                break
            except Exception:
                continue
        
        if not tags_obj:
            return metadata, None
        
        # Duration
        if hasattr(tags_obj.info, 'length'):
            metadata["duration"] = tags_obj.info.length
        
        # Helper to get first tag value
        def get_tag(tags, key: str) -> Optional[str]:
            vals = tags.get(key, [])
            return vals[0] if vals else None
        
        # Title
        if title := get_tag(tags_obj, "TITLE"):
            metadata["title"] = sanitize_string(title)
        
        # Artist
        if artist := get_tag(tags_obj, "ARTIST"):
            metadata["artist"] = sanitize_string(artist)
        
        # Album
        if album := get_tag(tags_obj, "ALBUM"):
            metadata["album"] = sanitize_string(album)
        
        # Album Artist
        if album_artist := get_tag(tags_obj, "ALBUMARTIST"):
            metadata["album_artist"] = sanitize_string(album_artist)
        elif metadata["artist"]:
            metadata["album_artist"] = metadata["artist"]
        
        # Genre
        if genre := get_tag(tags_obj, "GENRE"):
            metadata["genre"] = sanitize_string(genre)
        
        # Year
        if year := get_tag(tags_obj, "YEAR"):
            try:
                metadata["year"] = int(year)
            except ValueError:
                pass
        
        # Track Number
        if track := get_tag(tags_obj, "TRACKNUMBER"):
            try:
                metadata["track_number"] = int(track.split("/")[0])
            except ValueError:
                pass
        
        # Disc Number
        if disc := get_tag(tags_obj, "DISCNUMBER"):
            try:
                metadata["disc_number"] = int(disc.split("/")[0])
            except ValueError:
                pass
        
        # Extract artwork from embedded pictures
        pictures = tags_obj.get("PICT", [])
        for picture in pictures:
            if hasattr(picture, 'mime') and picture.mime.startswith("image/"):
                if getattr(picture, 'type', 3) == 3:  # Front cover
                    metadata["artwork_path"] = picture.data
                    break
        
        return metadata, metadata["artwork_path"]
        
    except Exception:
        return metadata, None


def _extract_m4a(path: str) -> Tuple[Dict[str, Any], Optional[str]]:
    """Extract M4A/MP4 metadata."""
    path_obj = Path(path)
    metadata = _get_default_metadata(path)
    
    try:
        tags = MP4(path)
        
        def get_mp4_tag(tag_obj, *keys) -> Optional[str]:
            for key in keys:
                val = tag_obj.get(key)
                if val:
                    if isinstance(val, list):
                        return str(val[0])
                    return str(val)
            return None
        
        # Duration
        if dur := get_mp4_tag(tags, "©dur", "md:\xa9duration"):
            try:
                metadata["duration"] = float(dur)
            except ValueError:
                pass
        
        # Title
        if title := get_mp4_tag(tags, "©nam", "title"):
            metadata["title"] = sanitize_string(title)
        
        # Artist
        if artist := get_mp4_tag(tags, "©ART", "ARTI", "artist"):
            metadata["artist"] = sanitize_string(artist)
        
        # Album
        if album := get_mp4_tag(tags, "©alb", "album"):
            metadata["album"] = sanitize_string(album)
        
        # Album Artist
        if album_artist := get_mp4_tag(tags, "©aRT", "artl"):
            metadata["album_artist"] = sanitize_string(album_artist)
        elif metadata["artist"]:
            metadata["album_artist"] = metadata["artist"]
        
        # Genre
        genre_map = {
            "9": "Alternative", "1": "Blues", "2": "Christian", "3": "Classical",
            "4": "Country", "6": "Dance/Electronic", "8": "Hip-Hop/Rap",
            "10": "Jazz", "11": "Metal", "12": "Pop", "13": "R&B/Soul",
            "14": "Reggae", "16": "Rock", "23": "Soundtrack",
        }
        if genre := get_mp4_tag(tags, "©gen", "genre"):
            metadata["genre"] = genre_map.get(genre, genre)
        
        # Year
        if year := get_mp4_tag(tags, "©yrr", "day"):
            try:
                metadata["year"] = int(year[:4]) if len(year) >= 4 else int(year)
            except ValueError:
                pass
        
        # Track
        if trkn := tags.get("trkn"):
            try:
                if isinstance(trkn, list) and trkn and isinstance(trkn[0], tuple):
                    metadata["track_number"] = trkn[0][0]
            except (IndexError, TypeError, ValueError):
                pass
        
        # Disc
        if disc := tags.get("disk"):
            try:
                if isinstance(disc, list) and disc and isinstance(disc[0], tuple):
                    metadata["disc_number"] = disc[0][0]
            except (IndexError, TypeError, ValueError):
                pass
        
        # Artwork
        covers = tags.get("covr") or tags.get("cover") or []
        if covers:
            metadata["artwork_path"] = covers[0]
        
        metadata["bitrate"] = 0
        metadata["sample_rate"] = 44100
        metadata["channels"] = 2
        
        return metadata, metadata["artwork_path"]
        
    except Exception:
        return metadata, None


def _extract_wav_or_aiff(path: str) -> Tuple[Dict[str, Any], Optional[str]]:
    """Extract WAV/AIFF metadata (limited, often no tags)."""
    path_obj = Path(path)
    metadata = _get_default_metadata(path)
    
    try:
        # Try based on file extension first
        ext = path_obj.suffix.lower()
        if ext == ".aif" or ext == ".aiff":
            tags = AIFF(path)
        elif ext == ".wav":
            tags = Wav(path)
        else:
            # Try generic mutagen.File for unknown formats
            from mutagen.file import File
            tags = File(path)
        
        # Try to get duration from audio info
        if hasattr(tags.info, 'frames') and hasattr(tags.info, 'sample_rate'):
            if tags.info.sample_rate > 0:
                metadata["duration"] = tags.info.frames / tags.info.sample_rate
        
        # WAV/AIFF tags are less standard, try common ones
        for key in ('title', 'TITLE', 'Title'):
            if title := tags.get(key):
                metadata["title"] = sanitize_string(str(title))
                break
        
        return metadata, metadata["artwork_path"]
        
    except Exception:
        return metadata, None


def extract_metadata(path: str) -> Tuple[Dict[str, Any], Optional[bytes]]:
    """
    Extract metadata from audio file.
    
    Returns:
        Tuple of (metadata_dict, artwork_data)
        artwork_data is raw bytes if found, None otherwise
    """
    path_obj = Path(path)
    extension = path_obj.suffix.lower()
    
    if extension == ".mp3":
        return _extract_mp3(path)
    elif extension in [".flac", ".oga", ".ogg"]:
        return _extract_flac_or_ogg(path)
    elif extension in [".m4a", ".mp4"]:
        return _extract_m4a(path)
    elif extension in [".wav", ".aif", ".aiff"]:
        return _extract_wav_or_aiff(path)
    else:
        # Try to analyze file content if extension doesn't help
        return _get_default_metadata(path), None


def save_artwork(data: bytes, output_dir: Path) -> Optional[str]:
    """
    Save artwork bytes to a file in the output directory.
    
    Args:
        data: Raw image data (bytes)
        output_dir: Directory to save artwork
    
    Returns:
        Path to saved artwork, or None if failed
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        hash_val = hashlib.md5(data).hexdigest()[:8]
        filename = f"artwork_{hash_val}.jpg"
        filepath = output_dir / filename
        
        # Write raw bytes (mutagen stores as JPEG/PNG)
        filepath.write_bytes(data)
        return str(filepath)
    except Exception:
        return None


def get_artwork_cache_dir() -> Path:
    """Get the default artwork cache directory."""
    import os
    app_data = Path(os.environ.get("APPDATA", ""))
    if app_data and app_data.exists():
        return app_data / "MusicPlayer" / "artwork"
    
    # Fallback to a relative directory
    return Path(__file__).parent.parent.parent / "music-player" / "artwork"


def get_duration_from_path(path: str) -> float:
    """Get duration from file path metadata (cached if available)."""
    try:
        metadata, _ = extract_metadata(path)
        if metadata.get("duration", 0) > 0:
            return metadata["duration"]
        
        # Fallback: use vlc if available
        try:
            import vlc
            media = vlc.Media(path)
            media.parse()
            duration_sec = media.get_duration() / 1000.0  # vlc returns ms
            return duration_sec
        except Exception:
            return 0.0
    except Exception:
        return 0.0