"""File scanning utilities."""
from __future__ import annotations
from pathlib import Path
from typing import Iterator, List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import src.backend.exceptions as exc


# Common audio file extensions
AUDIO_EXTENSIONS = {".mp3", ".flac", ".ogg", ".m4a", ".wav", ".aif", ".aiff", ".wma", ".aac", ".opus"}


def get_audio_files(path: str, recursive: bool = True) -> List[str]:
    """
    Get list of audio file paths under directory.
    
    Args:
        path: Directory path to scan
        recursive: Whether to scan subdirectories
    
    Returns:
        List of absolute file paths
    """
    path = Path(path)
    if not path.exists():
        return []
    
    if not path.is_dir():
        return [str(path)] if path.suffix.lower() in AUDIO_EXTENSIONS else []
    
    audio_files = []
    if recursive:
        # Recursive scan
        for file_path in path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in AUDIO_EXTENSIONS:
                audio_files.append(str(file_path))
    else:
        # Single-level scan
        for file_path in path.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in AUDIO_EXTENSIONS:
                audio_files.append(str(file_path))
    
    return sorted(audio_files)


class LibraryScanHandler(FileSystemEventHandler):
    """Handler for library file system events."""
    
    def __init__(self, callback=None):
        self.callback = callback
        self.changes_detected = False
    
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith(AUDIO_EXTENSIONS):
            self.changes_detected = True
            if self.callback:
                self.callback("file_created", str(event.src_path))
    
    def on_deleted(self, event):
        if event.is_directory:
            pass  # Directory delete handled differently
        elif event.src_path.lower().endswith(AUDIO_EXTENSIONS):
            self.changes_detected = True
            if self.callback:
                self.callback("file_deleted", str(event.src_path))
    
    def on_modified(self, event):
        # Don't trigger on metadata changes (rename files only)
        if not event.is_directory and event.src_path.lower().endswith(AUDIO_EXTENSIONS):
            # Check if it's a rename (mtime changed significantly)
            self.changes_detected = True
            if self.callback:
                self.callback("file_modified", str(event.src_path))


def start_library_watcher(library_paths: List[str], on_change_callback=None) -> Observer:
    """
    Start file watching for library directories.
    
    Args:
        library_paths: List of directories to watch
        on_change_callback: Callback (src_path, change_type) called on file changes
    
    Returns:
        Observer instance for later cleanup
    """
    event_handler = LibraryScanHandler(callback=on_change_callback)
    observer = Observer()
    observer.schedule(event_handler, library_paths[0], recursive=True)
    
    for path in library_paths[1:]:
        observer.schedule(event_handler, path, recursive=True)
    
    observer.start()
    return observer


def stop_library_watcher(observer: Observer):
    """Stop file watching."""
    observer.stop()
    observer.join()


def scan_directory_tree(root: str) -> Iterator[tuple[Path, str]]:
    """
    Recursively yield all directories and files under root.
    
    Yields:
        Tuple of (path, relative_to_root)
    """
    root = Path(root)
    
    if not root.exists():
        return
    
    for path in root.rglob("*"):
        yield path, str(path.relative_to(root))


def file_exists_in_path(file_path: str, library_paths: List[str]) -> bool:
    """Check if file path matches any library path prefix."""
    for lib_path in library_paths:
        lib_path = Path(lib_path).resolve()
        file_path = Path(file_path).resolve()
        
        # Check if file is under any library path, or if path is same prefix
        try:
            file_path.relative_to(lib_path)
            return True
        except ValueError:
            pass  # Not under this library path
    
    # Fallback: check if name matches
    file_stem = Path(file_path).stem.lower()
    for lib_path in library_paths:
        lib_path = Path(lib_path)
        if file_path.startswith(str(lib_path)) or lib_path.stem.lower() == file_stem:
            return True
    
    return False


def batch_scan(paths: List[str]) -> tuple[List[str], List[str]]:
    """
    Batch scan multiple directories, collecting new/changed files.
    
    Args:
        paths: Directories to scan
    
    Returns:
        Tuple of (new_files, all_files)
    """
    all_files = []
    for path in paths:
        if Path(path).exists():
            files = get_audio_files(path, recursive=True)
            all_files.extend(files)
    
    return sorted(all_files), sorted(all_files)


def limit_cache_size(cache_dir: Path, max_files: int = 100) -> None:
    """
    Limit cache directory to max_files files (delete oldest first).
    
    Args:
        cache_dir: Cache directory path
        max_files: Maximum number of artwork files
    """
    import os
    from datetime import datetime    
    from pathlib import Path
    
    if not cache_dir.exists():
        return
    
    cache_dir = Path(cache_dir)
    files = list(cache_dir.glob("artwork_*.jpg"))
    
    while len(files) > max_files:
        oldest = min(files, key=lambda p: p.stat().st_mtime)
        oldest.unlink()
        files = list(cache_dir.glob("artwork_*.jpg"))


def get_artwork_cache_dir() -> Path:
    """Get the default artwork cache directory."""
    import os
    app_data = Path(os.environ.get("APPDATA", ""))
    if app_data and app_data.exists():
        return app_data / "MusicPlayer" / "CACHE"
    
    # Fallback to a relative directory
    return Path(__file__).parent.parent.parent / "music-player CACHE"


def clean_temp_cache(cache_dir: Path, max_age_minutes: int = 60) -> None:
    """Remove artwork cache files older than max_age_minutes."""
    if not cache_dir.exists():
        return
    
    cache_dir = Path(cache_dir)
    
    for filepath in cache_dir.glob("artwork_*.jpg"):
        stat = filepath.stat()
        age = (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).total_seconds() / 60
        
        if age > max_age_minutes:
            filepath.unlink()


def ensure_artwork_cache_dir() -> Path:
    """Ensure artwork cache directory exists."""
    cache_dir = get_artwork_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

