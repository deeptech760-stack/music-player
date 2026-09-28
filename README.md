# Music Player

A simple Python music player built with PySide6 and a dark burgundy glass-inspired UI.

## Requirements

- Python 3.8+
- PySide6
- A modern operating system with a GUI

## Installation

1. Clone the repository:
\n\n    git clone https://github.com/yourusername/music-player.git
\n\n2. Navigate to the project directory:
\n\n    cd music-player
\n\n3. Install dependencies:
\n\n    python -m pip install -e .

## Running the Application

On Windows:
\n\n    run.bat
\n\nOn macOS:
\n\n    ./run.sh
\n\nOn Linux:
\n\n    chmod +x run.sh
\n\n    ./run.sh

## Directory Structure
\n\n    src/
\n        backend/
\n            services/
\n                library.py
\n                playback.py
\n                queue.py
\n                playlist.py
\n                settings.py
\n            models/
\n                __init__.py
\n\n        frontend/
\n            resources/
\n                style.qss
\n            components/
\n                artwork_label.py
\n                sidebar.py
\n                now_playing_bar.py
\n            main_window.py
\n
## Design
\n\n    Dark burgundy theme with subtle glassmorphism effects. The UI uses:
\n\n    - Background: `#1a0d14`
\n    - Surface: `#2d1321`
\n    - Border: `#4a1d3a`
\n\n    The sidebar is split from the main content with a right-edge border. All controls
\n    and input fields use a consistent accent scheme centered around deep burgundy.

## Contribution
\n\n    Feel free to modify the style and components in `src/frontend/resources/style.qss`.
\n\n    The main application is launched via `src/frontend/main_window.py` with `run.bat/run.sh` providing convenience wrappers.
\n\n    Add new music by populating the backend services, but keep the UI consistent with the existing dark burgundy aesthetic.
\n\n    The current implementation does not include backend data yet, so the app will show placeholder structures without actual metadata.
\n\n    If you need support for images, audio files, or external data sources, extend the `LibraryService` class in `src/backend/services/library.py`.

## Status
\n\n    This is a minimal working UI shell. The actual player functionality is not implemented.
\n\n    The main window is functional, but it has no content yet.
\n\n    The sidebar currently has empty item styling.
\n\n    The bottom now-playing bar includes basic controls, artwork, and text placeholders.
\n\n    The application can be launched successfully when dependencies are met and the correct Python entry script is used.
\n\n    This is ready for further development by a Python Qt or PySide6 developer.